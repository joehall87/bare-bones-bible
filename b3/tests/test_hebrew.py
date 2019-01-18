from ..hebrew import Hebrew


def test_transliteration():
	gen_1_1 = "בְּרֵאשִׁית בָּרָא אֱלֹהִים אֵת הַשָּׁמַיִם וְאֵת הָאָֽרֶץ"
	print(gen_1_1[:2].encode('raw_unicode_escape'))
	heb = Hebrew()
	tlit = heb.transliterate(gen_1_1)
	print(tlit)
	expected = "hello"
	assert tlit == expected