FROM python:3.10

WORKDIR /parse_images

COPY req.txt /parse_images
RUN pip install --upgrade pip && pip install -r /parse_images/req.txt

EXPOSE 8000

ADD ./parse /parse_images

# run app
CMD ["python", "main.py"]