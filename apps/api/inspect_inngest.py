import inngest
import sys

print('Inngest Version:', getattr(inngest, '__version__', 'N/A'))
print('Package Location:', inngest.__file__)
print('\nTop-level public attributes:')
attrs = sorted([x for x in dir(inngest) if not x.startswith('_')])
for attr in attrs:
    print(f'  {attr}')

print('\nChecking for FastAPI integration:')
if hasattr(inngest, 'fast_api'):
    print('  ✓ inngest.fast_api exists')
    print('  Contents:', dir(inngest.fast_api))
else:
    print('  ✗ inngest.fast_api does NOT exist')
    
if hasattr(inngest, 'asgi'):
    print('  ✓ inngest.asgi exists')
    print('  Contents:', dir(inngest.asgi))
else:
    print('  ✗ inngest.asgi does NOT exist')
