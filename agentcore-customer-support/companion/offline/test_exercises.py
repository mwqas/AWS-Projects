import unittest
from validation import validate_request, format_order
from loyalty import quote

class RequestTests(unittest.TestCase):
    def test_valid(self): self.assertTrue(validate_request({"prompt":"Hi"})["valid"])
    def test_invalid_types(self):
        for item in (None, [], 12, "text"):
            with self.subTest(item=item): self.assertFalse(validate_request(item)["valid"])
    def test_invalid_prompts(self):
        for item in (None, 12, "", "   ", []):
            with self.subTest(item=item): self.assertFalse(validate_request({"prompt":item})["valid"])
    def test_missing_tracking(self):
        self.assertIn("unavailable", format_order({"order_id":"O1", "status":"shipped"}))

class LoyaltyTests(unittest.TestCase):
    def test_reference_quote(self):
        result=quote(4250,"Gold","150.00")
        self.assertEqual((result["points_redeemed"],result["final_total"],result["remaining_points"],result["balance_after_purchase"]),(4000,"99.00",250,349))
    def test_block_boundary(self):
        self.assertEqual(quote(499,"Silver",100)["points_redeemed"],0)
        self.assertEqual(quote(500,"Silver",100)["points_redeemed"],500)
    def test_cap(self):
        self.assertEqual(quote(10000,"Silver",20)["points_redeemed"],1000)
        self.assertEqual(quote(10000,"Silver",9)["points_redeemed"],0)
    def test_zero(self): self.assertEqual(quote(0,"Gold",0)["final_total"],"0.00")
    def test_invalid_points(self):
        for p in (-1,True,1.5):
            with self.subTest(p=p),self.assertRaises(ValueError):quote(p,"Gold",10)
    def test_invalid_money(self):
        for a in ("NaN","Infinity","-1","1.234","bad"):
            with self.subTest(a=a),self.assertRaises(ValueError):quote(0,"Gold",a)
    def test_invalid_policy(self):
        with self.assertRaises(ValueError): quote(0,"Diamond",10)
        with self.assertRaises(ValueError): quote(0,"Gold",10,"unknown")
    def test_earning(self):
        self.assertEqual(quote(0,"Silver","1.99","device")["points_earned"],3)

if __name__ == "__main__": unittest.main()
