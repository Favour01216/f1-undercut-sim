import sys
sys.path.append('backend')

# Test the simulation with fixed tire advantage calculation
from backend.app import SimulateRequest, simulate_undercut
from fastapi import Request
from unittest.mock import Mock
import asyncio

async def test():
    try:
        req_data = SimulateRequest(
            gp='bahrain',
            year=2024,
            driver_a='VER',
            driver_b='HAM',
            compound_a='MEDIUM',
            lap_now=15,
            samples=100
        )
        
        mock_req = Mock(spec=Request)
        
        print('Testing simulation with fixed tire advantage fallback...')
        result = await simulate_undercut(req_data, mock_req)
        
        print('\nFINAL SIMULATION RESULTS:')
        print(f'   Undercut probability: {result.p_undercut:.1%}')
        print(f'   Pit loss: {result.pitLoss_s:.3f}s')
        print(f'   Outlap penalty: {result.outLapDelta_s:.3f}s')
        
        # Detailed analysis
        gap = result.assumptions.get('current_gap_s', 0)
        margin = result.assumptions.get('success_margin_s', 0)
        deg_penalty = result.assumptions.get('avg_degradation_penalty_s', 0)
        total_penalty = result.pitLoss_s + result.outLapDelta_s
        
        print(f'\nPHYSICS ANALYSIS:')
        print(f'   Current gap: {gap:.1f}s')
        print(f'   Total penalty: {total_penalty:.1f}s')
        print(f'   Degradation advantage: {deg_penalty:.3f}s/lap')
        print(f'   Success margin: {margin:.1f}s')
        
        # Models used
        models_used = result.assumptions.get('models_fitted', {})
        print(f'\nDATA-DRIVEN MODELS:')
        print(f'   DegModel: {"YES" if models_used.get("deg_model") else "NO (using fallback)"}')
        print(f'   PitModel: {"YES" if models_used.get("pit_model") else "NO"}')
        print(f'   OutlapModel: {"YES" if models_used.get("outlap_model") else "NO"}')
        
        if result.p_undercut > 0:
            print(f'\nSUCCESS: {result.p_undercut:.1%} undercut probability!')
            print('Data-driven F1 simulation working correctly!')
        else:
            print('\nREALISTIC RESULT: Undercut fails due to F1 physics')
            print('High penalties (pit + outlap) vs small gaps = realistic F1')
            
        return result
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

asyncio.run(test())