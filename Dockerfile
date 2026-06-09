FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY . .

# Sync dependencies
RUN uv sync

# Expose port
EXPOSE 7860

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["uv", "run", "python", "main.py"]
