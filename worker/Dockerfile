# FROM python:3
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy to the working directory
COPY . .

RUN python -m pip install -r requirements.txt

# python3 -m venv myenv
# source myenv/bin/activate

# Set the entry point for the container
CMD [ "python", "./worker.py" ]