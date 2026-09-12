import streamlit as st
from dotenv import load_dotenv
load_dotenv()
from youtube import get_video_info
from transcript import get_transcript
from claim_analyzer import analyze_claim
from content_analyzer import analyze_content
from verdict import generate_verdict

st.set_page_config(page_title="TruthClick AI", page_icon="🎯", layout="wide")

st.title("🎯 TruthClick AI")
st.caption("Does the video deliver what the title promises?")

url = st.text_input("YouTube video URL", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Analyze Video", type="primary", disabled=not url.strip()):
    try:
        with st.status("Analyzing video...", expanded=True) as status:
            st.write("Fetching video information...")
            video = get_video_info(url)

            st.write("Getting transcript...")
            transcript = get_transcript(video["video_id"])

            if not transcript:
                raise ValueError("No usable transcript was found for this video.")

            st.write("Understanding the title claim...")
            claim = analyze_claim(video["title"], video.get("thumbnail"))

            st.write("Comparing claim with video content...")
            content = analyze_content(claim, transcript)

            st.write("Generating final verdict...")
            result = generate_verdict(claim, content)
            status.update(label="Analysis complete", state="complete")

        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(video["thumbnail"], use_container_width=True)
        with col2:
            st.subheader(video["title"])
            st.write(f"**Channel:** {video['channel']}")
            st.write(f"**Duration:** {video['duration']}")
            st.write(f"**URL:** {video['url']}")

        verdict = result["verdict"]
        if verdict == "CLICKBAIT":
            st.error("🔴 CLICKBAIT")
        elif verdict == "NON_CLICKBAIT":
            st.success("🟢 NON-CLICKBAIT")
        else:
            st.warning("🟡 INCONCLUSIVE")

        st.metric("Confidence", f"{result['confidence'] * 100:.0f}%")

        st.subheader("Main Claim")
        st.write(claim["claim"])
        st.caption(claim.get("expected_content", ""))

        st.subheader("Why?")
        st.write(result["reason"])

        st.subheader("Evidence")
        segments = content.get("relevant_segments", [])
        if segments:
            for seg in segments:
                st.markdown(f"**{seg['start_display']} → {seg['end_display']} — {seg['topic']}**")
                st.write(seg["evidence"])
                if seg.get("youtube_url"):
                    st.link_button("Open at this timestamp", f"https://www.youtube.com/watch?v={video['video_id']}&t={int(seg['start'])}s")
        else:
            st.info("No strong supporting segment was found.")

        with st.expander("Technical analysis"):
            st.json({"claim": claim, "content_analysis": content, "verdict": result})

    except Exception as exc:
        st.error(str(exc))
