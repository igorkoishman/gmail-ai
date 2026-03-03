# Gemini CLI - Todo List

This list reflects the last known state of our development tasks.

1.  [completed] Add a new method `get_ai_classified_count` to `database_engine.py` to count emails that have `ai_category` not null and `manual_category` null.
2.  [completed] Modify the `teach_with_gemini` method in `main_pro.py` to:
    a. Get the current count of AI-classified emails.
    b. Calculate the number of additional emails needed to reach the 2000 Gemini-classified target.
    c. Fetch only this calculated number of emails from the database using `get_emails_for_ai`.
    d. Proceed with Gemini classification for these fetched emails.
3.  [completed] (Completed) Modify the `teach_with_gemini` method in `main_pro.py` to set `reclassify_ai_labels=False` when calling `self.db.get_emails_for_ai`.
4.  [completed] (Completed) Ensure the `limit` for `teach_with_gemini` is set to 2000 for Gemini processing. (Note: The `limit` in the method signature is a default, the actual target is now handled by internal logic.)
5.  [completed] (Completed) Orchestrate the calls to `teach_with_gemini` and `predict_all` in `main_pro.py` to implement the two-stage classification workflow.
6.  [completed] (Completed) Review the existing error handling in `teach_with_gemini` to confirm that emails from failed Gemini batches are correctly left uncategorized for future attempts.
7.  [completed] (Completed) Add database indexes to the `emails` table on `manual_category` and `ai_category` to improve query performance.
