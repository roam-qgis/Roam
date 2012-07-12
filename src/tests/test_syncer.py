from mock import patch
from syncing import syncer
from unittest import TestCase, main
from subprocess import Popen

class testImageSyncer(TestCase):
    @patch('os.path.exists', return_value=False)
    def test_image_path_not_found_return_0_images(self, mock_exists):
        state, msg = syncer.syncImages()
        self.assertEqual(state,"Pass")
        self.assertEqual(msg,"Images uploaded: 0")

    @patch('os.path.exists', return_value=True)
    @patch.object(Popen, 'communicate', return_value=("","Error"))
    def test_return_fail_on_stderr(self, mock_sub, mock_exists ):
        state, msg = syncer.syncImages()
        self.assertEqual(state,"Fail")
        self.assertEqual(msg,"Error")

    @patch('os.path.exists', return_value=True)
    @patch.object(Popen, 'communicate', return_value=("Not Error",""))
    def test_return_pass_on_stdout(self, mock_sub, mock_exists ):
        state, msg = syncer.syncImages()
        self.assertEqual(state,"Pass")
        self.assertEqual(msg,"Not Error")


if __name__ == "__main__":
    main()
        
