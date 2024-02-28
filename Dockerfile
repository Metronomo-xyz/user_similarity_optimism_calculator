FROM python:3.11.8-bookworm

WORKDIR /user_similarity_optimism_calculator

COPY . .

RUN pip install -r requirements.txt

workdir ../

CMD ["python", "-m", "user_similarity_optimism_calculator"]