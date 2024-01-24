from InstructorEmbedding import INSTRUCTOR

if __name__ == "__main__":
	print("Fetching instructor data...")
	xl = INSTRUCTOR('hkunlp/instructor-xl')
	large = INSTRUCTOR('hkunlp/instructor-large')
	print("Instructor data fetched successfully.")