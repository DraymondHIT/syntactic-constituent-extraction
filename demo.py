from pipeline import pipeline

with open("test/sample.txt", "r") as f:
    corpus = f.read().splitlines()
f.close()

for index, text in enumerate(corpus):
    doc = pipeline(text)
    # doc.question_answer_generation()
    print(f"========={index}=========")
    print(doc)
