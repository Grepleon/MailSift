import weed_out.black_and_white_list as baw

baw_list = baw.BlackAndWhiteList()
baw_list.set_text("""

""", "*.com")
baw_list.process_text()
print(baw_list.to_send())