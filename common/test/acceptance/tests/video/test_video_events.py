
import json

from ..helpers import EventsTestMixin
from .test_video_module import VideoBaseTest

from opaque_keys.edx.keys import UsageKey


class VideoEventsTest(EventsTestMixin, VideoBaseTest):
    """ Test video player event emission """

    def test_video_control_events(self):
        """
        Scenario: Video component is rendered in the LMS in Youtube mode without HTML5 sources
        Given the course has a Video component in "Youtube" mode
        And I play the video
        And I watch 5 seconds of it
        And I pause the video
        Then a "load_video" event is emitted
        And a "play_video" event is emitted
        And a "pause_video" event is emitted
        """
        load_video_promise = self.create_event_of_type_promise('load_video')

        self.navigate_to_video()

        load_video_event = load_video_promise.fulfill()

        self.assert_payload_contains_ids(load_video_event)
        self.assert_event_matches({'event_type': 'load_video'}, load_video_event)

        play_video_promise = self.create_event_of_type_promise('play_video')
        pause_video_promise = self.create_event_of_type_promise('pause_video')

        self.video.click_player_button('play')
        self.video.wait_for_position('0:05')
        self.video.click_player_button('pause')

        play_video_event = play_video_promise.fulfill()
        self.assert_valid_control_event_at_time(play_video_event, 0)

        pause_video_event = pause_video_promise.fulfill()
        self.assert_valid_control_event_at_time(pause_video_event, self.video.seconds)

    def assert_payload_contains_ids(self, video_event):
        """
        Video events should all contain "id" and "code" attributes in their payload.

        This function asserts that those fields are present and have correct values.
        """
        video_descriptors = self.course_fixture.get_nested_xblocks(category='video')
        video_desc = video_descriptors[0]
        video_locator = UsageKey.from_string(video_desc.locator)

        expected_event_pattern = {
            'event': {
                'id': video_locator.html_id(),
                'code': '3_yD_cEKoCk'
            }
        }
        self.assert_event_matches(expected_event_pattern, video_event)

    def assert_valid_control_event_at_time(self, video_event, time_in_seconds):
        """
        Video control events should contain valid ID fields and a valid "currentTime" field.

        This function asserts that those fields are present and have correct values.
        """
        self.assert_payload_contains_ids(video_event)
        current_time = json.loads(video_event['event'])['currentTime']
        self.assertAlmostEqual(current_time, time_in_seconds, delta=0.5)
