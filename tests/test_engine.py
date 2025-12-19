import unittest
from nocturn_studio.hardware.device import MockNocturnDevice
from nocturn_studio.model.mapping import Mapping, MappingTarget, TargetType, MappingMode
from nocturn_studio.engine.mapper import MappingEngine
from nocturn_studio.daw.midi import MockMidiOutput

class TestMappingEngine(unittest.TestCase):
    def setUp(self):
        self.device = MockNocturnDevice()
        self.midi = MockMidiOutput()
        self.engine = MappingEngine(self.midi)
        
        # Connect device to engine
        self.device.add_event_listener(self.engine.handle_event)
        self.device.connect()

    def test_encoder_integration(self):
        # 1. Setup a mapping for "encoder_1" -> CC 10 on Channel 1
        mapping = Mapping(
            source_id="encoder_1",
            target=MappingTarget(TargetType.MIDI_CC, channel=0, identifier=10),
            min_val=0,
            max_val=127
        )
        self.engine.load_mappings({"encoder_1": mapping})
        
        # 2. Simulate turns
        # Initial value is 0. Turn +5.
        self.device.simulate_turn("encoder_1", 5)
        
        # Check MIDI
        self.assertEqual(len(self.midi.sent_messages), 1)
        msg = self.midi.sent_messages[0]
        self.assertEqual(msg.status, 0xB0) # Channel 1 CC
        self.assertEqual(msg.data1, 10)    # CC Number
        self.assertEqual(msg.data2, 5)     # Value
        
        # 3. Turn more (+10)
        self.device.simulate_turn("encoder_1", 10)
        
        self.assertEqual(len(self.midi.sent_messages), 2)
        msg = self.midi.sent_messages[1]
        self.assertEqual(msg.data2, 15)    # 5 + 10 = 15

if __name__ == '__main__':
    unittest.main()
