FROM python:3.10-slim

RUN apt update && apt install -y libgl1-mesa-glx libglib2.0-0

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt

# 1. download the autofix tool
RUN pip install opencv-fixer==0.2.5
# 2. execute
RUN python -c "from opencv_fixer import AutoFix; AutoFix()"
 


COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
