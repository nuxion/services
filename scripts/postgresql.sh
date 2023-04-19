#!/bin/bash


docker run --rm --name services-postgres \
	-e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
	-p 127.0.0.1:5432:5432  postgres:14.7-alpine
