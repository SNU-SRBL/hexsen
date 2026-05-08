import torch
import time
from model.mlstm_fcn import MLSTM_FCN

def benchmark(device, model, input_tensor, iters=100):
    model = model.to(device)
    input_tensor = input_tensor.to(device)
    model.eval()

    # Warm-up (important!)
    with torch.no_grad():
        for _ in range(10):
            _ = model(input_tensor)
        if device.type == 'cuda':
            torch.cuda.synchronize()

    # Timing
    start = time.time()
    with torch.no_grad():
        for _ in range(iters):
            _ = model(input_tensor)
        if device.type == 'cuda':
            torch.cuda.synchronize()
    end = time.time()

    elapsed_ms = (end - start) * 1000 / iters
    return elapsed_ms


if __name__ == "__main__":
    # Model & input
    model = MLSTM_FCN()
    input_tensor = torch.rand(360, 4, 50)

    # CPU benchmark
    cpu_time = benchmark(
        device=torch.device("cpu"),
        model=model,
        input_tensor=input_tensor
    )

    # CUDA benchmark (if available)
    if torch.cuda.is_available():
        gpu_time = benchmark(
            device=torch.device("cuda:0"),
            model=model,
            input_tensor=input_tensor
        )
    else:
        gpu_time = None

    print(f"CPU inference time  : {cpu_time:.3f} ms / iter")
    if gpu_time is not None:
        print(f"CUDA inference time : {gpu_time:.3f} ms / iter")
