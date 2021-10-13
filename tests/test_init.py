import os

def test_load_dotenv():
	# verify that the environment variable is now set
	meaning_of_life = os.environ.get('MEANING_OF_LIFE')
	assert meaning_of_life in ['02', '12', '22', '32' '42']
