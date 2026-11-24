import os
import sys
import unittest
from PIL import Image, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

import lostfound
from lostfound.extras import verify_ownership, is_blurry, check_duplicate


class TestLostFound(unittest.TestCase):
    def test_text_only_search(self):
        res = lostfound.search_lost_item("blue water bottle", k=3)
        self.assertTrue(len(res) > 0)
        self.assertEqual(res[0]["item_id"], "ITEM_001")
        for key in ("item_id", "score", "location", "date"):
            self.assertIn(key, res[0])

    def test_image_only_search(self):
        res = lostfound.search_lost_item("", image_path="data/items/images/ITEM_001_2.jpg", k=3)
        self.assertEqual(res[0]["item_id"], "ITEM_001")

    def test_multimodal_rerank_search(self):
        res = lostfound.search_lost_item(
            "blue bottle",
            image_path="data/items/images/ITEM_001_2.jpg",
            location="Library",
            k=5,
        )
        self.assertEqual(res[0]["item_id"], "ITEM_001")
        self.assertTrue(res[0]["notify"])

    def test_ownership_verification(self):
        ok = verify_ownership("ITEM_001", "there is a dent on the bottom left")
        bad = verify_ownership("ITEM_001", "it has a batman sticker")
        self.assertTrue(ok["verified"])
        self.assertFalse(bad["verified"])

    def test_blur_and_duplicate_checks(self):
        sharp, _ = is_blurry("data/items/images/ITEM_001_1.jpg", threshold=1200.0)
        self.assertFalse(sharp)

        blur_path = os.path.join(BASE_DIR, "data/items/images/blur_test.jpg")
        Image.open(os.path.join(BASE_DIR, "data/items/images/ITEM_001_1.jpg")).filter(
            ImageFilter.GaussianBlur(5)
        ).save(blur_path)
        blurry, _ = is_blurry(blur_path, threshold=1200.0)
        self.assertTrue(blurry)

        dup = check_duplicate("Blue stainless steel water bottle with black cap", "data/items/images/ITEM_001_1.jpg")
        self.assertTrue(dup["is_duplicate"])


if __name__ == "__main__":
    unittest.main()
