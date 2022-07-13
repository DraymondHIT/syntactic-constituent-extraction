from pipeline import pipeline

with open("sample.txt", "r") as f:
    corpus = f.readlines()
f.close()

for index, text in enumerate(corpus):
    doc = pipeline(text)
    print(f"========={index}=========")
    print(doc)
