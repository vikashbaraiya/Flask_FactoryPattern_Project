# Stage 1: Builder
FROM python:3.10.12-alpine AS builder

# Set working directory
WORKDIR /Project_Main

# Install build tools and essential libraries for compiling dependencies
RUN apk add --no-cache gcc musl-dev python3-dev libffi-dev libxml2-dev libxslt-dev

# Create a virtual environment
RUN python3 -m venv venv
ENV VIRTUAL_ENV=/Project_Main/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Upgrade setuptools, pip, and wheel
RUN pip install --upgrade pip setuptools wheel

# Copy dependency file and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Stage 2: Runtime
FROM python:3.10.12-alpine AS runner

# Set working directory
WORKDIR /Project_Main

# Copy the virtual environment and project files
COPY --from=builder /Project_Main/venv /Project_Main/venv
COPY . .

# Configure environment variables
ENV VIRTUAL_ENV=/Project_Main/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV FLASK_APP=run.py

# Expose the application's port
EXPOSE 5000

# Define the default command for the container
CMD ["gunicorn", "--bind", ":5000", "--workers", "2", "run:app"]
