import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
from torch.vision import transforms
from models.vae import VAE

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Using device: {DEVICE}')

# --- Model and Data Dimensions ---
IMAGE_SIZE = 128  # Input image resolution (e.g., 128x128 pixels)
IN_CHANNELS = 3   # Number of input channels (e.g., 3 for RGB or raw maps: iterations, magnitudes, angles)
LATENT_DIM = 128  # Dimensionality of the VAE's latent space

# --- Training Hyperparameters ---
BATCH_SIZE = 64     # Number of samples per training batch
LEARNING_RATE = 1e-4 # Optimizer learning rate
NUM_EPOCHS = 50     # Number of full passes through the dataset during training

model = VAE(in_channels=IN_CHANNELS, latent_dim=LATENT_DIM).to(DEVICE)
optimizer = optim.Adam(model.parameters(), lr = LEARNING_RATE)

def re_loss_fn(reconstruction, data):
    return F.mse_loss(reconstruction, data, reduction='sum')

def kl_loss_fn(mean, logv):
    return -0.5 * torch.sum(1 + logv - mean.pow(2) - torch.exp(logv))

if __name__ == '__main__':
    # Load, preprocess and build dataset placeholder
    dummy_data = torch.randn(100, IN_CHANNELS, IMAGE_SIZE, IMAGE_SIZE) # 100 dummy images
    dataloader = DataLoader(TensorDataset(dummy_data), batch_size=BATCH_SIZE, shuffle=True)

    for epoch in range(NUM_EPOCHS):
        model.train()
        total_re_loss = 0
        total_kl_loss = 0
        total_sm_loss = 0

        for batch_idx, (data,) in enumerate(dataloader):
            #Forward pass
            data = data.to(DEVICE)
            reconstruction, mean, logv = model(data)
            #Calculate reconstruction, KL divergence and summed losses
            re_loss = re_loss_fn(reconstruction, data)
            kl_loss = kl_loss_fn(mean, logv)
            sm_loss = re_loss + kl_loss
            #Backward pass
            optimizer.zero_grad()
            sm_loss.backward()
            optimizer.step()
            #Log batch loss
            total_re_loss += re_loss.item()
            total_kl_loss += kl_loss.item()
            total_sm_loss += sm_loss.item()
        
        num_samples = len(dataloader.dataset)
        print(f'Epoch: {epoch + 1}')
        print(f'SM Loss: {total_sm_loss / num_samples}')
        print(f'RE Loss: {total_re_loss / num_samples}')
        print(f'KL Loss: {total_kl_loss / num_samples}')

    torch.save(model.state_dict(), 'vae_fractal_model.pth')