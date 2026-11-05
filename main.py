import weed_out.ai_checker as ai

baw_list = ai.AIChecker()
baw_list.set_text("""

""", "*.com")
baw_list.process_text()
print(baw_list.to_send())
baw_list.learn(True)