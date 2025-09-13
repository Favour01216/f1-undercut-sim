#!/usr/bin/env python3
import sys
import os
sys.path.append('backend')

from app import get_or_fit_models

print('Testing model fitting for Bahrain 2024...')
try:
    models = get_or_fit_models('bahrain', 2024)
    print('Models fitted:')
    for key, model in models.items():
        print(f'  {key}: {model is not None}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()