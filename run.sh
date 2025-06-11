#!/bin/bash
export $(cat .env | xargs)
python example.py