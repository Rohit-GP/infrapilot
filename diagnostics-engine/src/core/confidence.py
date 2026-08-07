from src.core.models import ProbeStatus

def calculate_confidence(
    status: ProbeStatus,
    latency_ms: float | None = None,
):
    
    score = 100
    
    # Base confidence from probe status
    if status == ProbeStatus.OK:
        score = 100
        
    elif status == ProbeStatus.DEGRADED:
        score = 80
        
    elif status == ProbeStatus.FAILED:
        score = 60
        
    elif status == ProbeStatus.ERROR:
        score = 30
        
    # Reduce confidence for high latency
    if latency_ms is not None:
        
        if latency_ms > 100:
            score -= 5
            
        if latency_ms > 300:
            score -= 10
            
        if latency_ms > 1000:
            score -= 15
            
    return max(0, score)

    