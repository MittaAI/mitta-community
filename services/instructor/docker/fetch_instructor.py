from InstructorEmbedding import INSTRUCTOR

if __name__ == "__main__":
	print("Fetching instructor data...")
	xl = INSTRUCTOR('hkunlp/instructor-xl')
	large = INSTRUCTOR('hkunlp/instructor-large')
	embeddings = xl.encode("install").tolist()
	embeddings = large.encode("install").tolist()
	print("Instructor data fetched successfully.")