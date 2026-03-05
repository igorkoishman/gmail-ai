from main_pro import ProClassifier

pc = ProClassifier()
test_cases = [
    ('igorkoishman@gmail.com', 'Some Category', 'Me expected'),
    ('marina0020@gmail.com', 'Me', 'Marina expected'),
    ('noreply@github.com', 'Survey', 'Work/Professional expected'),
    ('ebay@ebay.com', 'Other', 'Shopping/Promotions expected'),
    ('promotion@aliexpress.com', 'Marina', 'Ali express adds expected'),
    ('stranger@gmail.com', 'Me', 'Other/Review expected (Fallback)'),
    ('stranger@gmail.com', 'Marina', 'Other/Review expected (Fallback)'),
    ('stranger@gmail.com', 'Work/Professional', 'Work/Professional expected (No fallback)')
]

for sender, ml_pred, expected in test_cases:
    # Simulate the loop logic
    hard_cat = pc._get_hard_rule(sender)
    final_cat = ml_pred
    if hard_cat:
        final_cat = hard_cat
    else:
        if final_cat == "Me" and 'igorkoishman@gmail.com' not in sender.lower():
            final_cat = "Other/Review"
        elif final_cat == "Marina" and 'marina0020@gmail.com' not in sender.lower():
            final_cat = "Other/Review"
    print(f"Sender: {sender:30} | ML: {ml_pred:20} -> Final: {final_cat:20} | {expected}")
