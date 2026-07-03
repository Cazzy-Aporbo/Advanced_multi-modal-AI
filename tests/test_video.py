from advanced_multimodal_ai.contracts import VideoCleaningRequest, VideoPacketRequest
from advanced_multimodal_ai.video import build_video_cleaning_response, build_video_packet


def test_video_packet_uses_transcript_windows():
    response = build_video_packet(
        VideoPacketRequest(
            clip_id="clip-02",
            duration_ms=5000,
            transcript=[
                {"token": "good", "start_ms": 100, "end_ms": 300},
                {"token": "morning", "start_ms": 320, "end_ms": 620},
                {"token": "everyone", "start_ms": 2500, "end_ms": 2900},
            ],
            frames=[
                {
                    "index": 0,
                    "timestamp_ms": 250,
                    "motion_score": 0.1,
                    "focus_score": 0.8,
                    "brightness": 0.5,
                },
                {
                    "index": 1,
                    "timestamp_ms": 2600,
                    "motion_score": 0.4,
                    "focus_score": 0.7,
                    "brightness": 0.6,
                },
            ],
        )
    )
    assert len(response.evidence_windows) == 2
    assert response.evidence_windows[0].transcript_excerpt.startswith("good morning")


def test_video_cleaning_finds_fillers_and_silence():
    response = build_video_cleaning_response(
        VideoCleaningRequest(
            clip_id="clip-03",
            duration_ms=6000,
            transcript=[
                {"token": "uh", "start_ms": 0, "end_ms": 150},
                {"token": "we", "start_ms": 1000, "end_ms": 1200},
                {"token": "start", "start_ms": 1250, "end_ms": 1500},
                {"token": "now", "start_ms": 3200, "end_ms": 3400},
            ],
        )
    )
    reasons = {span.reason for span in response.removed_spans}
    assert "filler_word" in reasons
    assert "silence_gap" in reasons
