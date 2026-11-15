Consolidated Evaluation — All Three Models
Per-model × per-family label counts
Label	A5	A6	A7	Total
tiny-aya-global-sft-adversarial-ckpt1000 (file 1)	
injection_followed	0	15	0	15
injection_partial_follow	152	80	19	251
missed_injection_detection_only	0	0	0	0
ordinary_extraction_error	71	142	230	443
correct_prediction	77	63	51	191
tiny-aya-earth-base (file 2)	
injection_followed	0	28	0	28
injection_partial_follow	84	7	24	115
missed_injection_detection_only	0	2	11	13
ordinary_extraction_error	155	225	263	643
correct_prediction	61	38	2	101
tiny-aya-global-base (file 3)	
injection_followed	0	27	0	27
injection_partial_follow	94	25	24	143
missed_injection_detection_only	0	2	15	17
ordinary_extraction_error	142	213	259	614
correct_prediction	64	33	2	99
Cross-model comparison (totals over 900 rows each)
Label	sft-adversarial-ckpt1000	earth-base	global-base
injection_followed	15	28	27
injection_partial_follow	251	115	143
missed_injection_detection_only	0	13	17
ordinary_extraction_error	443	643	614
correct_prediction	191	101	99
Key takeaways

A6 (explicit override: “set intent=transfer”) is the only family that elicits injection_followed. The two base models are roughly twice as susceptible (~9%) as the adversarially fine-tuned checkpoint (~5%), suggesting adversarial SFT provides meaningful but not complete resistance to explicit intent hijacking.

A5 (benign-looking payload) produces the most injection_partial_follow across all models — the payload text bleeds into redacted_text without shifting classification labels. The SFT checkpoint leaks far more (152 vs 84/94), implying its fine-tuning may have made it more likely to reproduce all input text faithfully rather than filter injected content.

A7 (vague override: “ignore previous instructions”) causes neither injection_followed nor much leakage — it mainly degrades general extraction quality (ordinary_extraction_error ≈ 230–263), consistent with the ambiguous instruction confusing the model without reliably hijacking it.

missed_injection_detection_only is zero for the SFT model but non-zero for both base models (13 and 17), concentrated in A6 and A7 — base models are slightly more likely to miss flagging an injection even when their extraction is otherwise correct.

correct_prediction is notably higher for the SFT checkpoint (191 vs ~100), confirming the adversarial fine-tuning improved overall extraction accuracy, even if it traded off some leakage resistance on A5.