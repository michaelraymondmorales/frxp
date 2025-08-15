import torch
import torch.nn as nn
import torch.nn.functional as F

class VAE_Encoder(nn.Module):
    def __init__(self, latent_dim=128, in_channels=3):
        super(VAE_Encoder, self.__init__())

        #input (Batch_Size, 3, 128, 128)
        #kernel_size = 4, stride = 2, padding = 1 halves spatial dimension
        #output_dim  = (input_dim - kernel_size + 2 * padding) / stride + 1
    
        #L1: 128x128 -> 64X64
        self.conv1 = nn.Conv2d(in_channels, 32, kernel_size = 4, stride = 2, padding = 1)
        self.bn1 = nn.BatchNorm2d(32)

        #L2: 64x64 -> 32x32
        self.conv2 = nn.Conv2d(32, 64, kernel_size = 4, stride = 2, padding = 1)
        self.bn2 = nn.BatchNorm2d(64)

        #L3: 32x32 -> 16X16
        self.conv3 = nn.Conv2d(64, 128, kernel_size = 4, stride = 2, padding = 1)
        self.bn3 = nn.BatchNorm2d(128)

        #L4: 16X16 -> 8x8
        self.conv4 = nn.Conv2d(128, 256, kernel_size = 4, stride = 2, padding = 1)
        self.bn4 = nn.BatchNorm2d(256)

        #L5: 8x8 -> 4x4
        self.conv5 = nn.Conv2d(256, 512, kernel_size = 4, stride = 2, padding = 1)
        self.bn5 = nn.BatchNorm2d(512)

        #Flattened output size from last Conv layer will be 4 * 4 * 512
        #Fully connected layers for mean and log-variance
        self.fc_size = 4 * 4 * 512
        self.fc_mean = nn.Linear(self.fc_size, latent_dim)
        self.fc_logv = nn.Linear(self.fc_size, latent_dim)

    def forward(self, x):
        x = F.relu(self.bn1(self.conv1(x))) # 128 -> 64
        x = F.relu(self.bn2(self.conv2(x))) # 64 -> 32
        x = F.relu(self.bn3(self.conv3(x))) # 32 -> 16
        x = F.relu(self.bn4(self.conv4(x))) # 16 -> 8
        x = F.relu(self.bn5(self.conv5(x))) # 8 -> 4

        x = x.view(-1, self.fc_size)
        mean = self.fc_mean(x)
        logv = self.fc_logv(x)
        return mean, logv

class VAE_Decoder(nn.Module):
    def __init__(self, latent_dim=128, out_channels=3):
        super(VAE_Decoder, self).__init__()

        #input (Batch_Size, latent_dim)
        #Reshaping latent vector to match the size of the encoder's L5
        self.fc_unflatten = nn.Linear(latent_dim, 4 * 4 * 512)

        #L1: 4x4 -> 8x8
        self.conv_t1 = nn.ConvTranspose2d(512, 256, kernel_size = 4, stride = 2, padding = 1)
        self.bn1 = nn.BatchNorm2d(256)

        #L2: 8x8 -> 16x16
        self.conv_t2 = nn.ConvTranspose2d(256, 128, kernel_size = 4, stride = 2, padding = 1)
        self.bn2 = nn.BatchNorm2d(128)

        #L3: 16x16 -> 32x32
        self.conv_t3 = nn.ConvTranspose2d(128, 64, kernel_size = 4, stride = 2, padding = 1)
        self.bn3 = nn.BatchNorm2d(64)

        #L4: 32x32 -> 64x64
        self.conv_t4 = nn.ConvTranspose2d(64, 32, kernel_size = 4, stride = 2, padding = 1)
        self.bn4 = nn.BatchNorm2d(32)

        #L5: 64x64 -> 128x128
        self.conv_t5 = nn.ConvTranspose2d(32, out_channels, kernel_size = 4, stride = 2, padding = 1)

    def forward(self, z):
        #Reshape latent vector into feature map
        #Reshape to (Batch_Size, Channels, H, W)
        #Output layer using sigmoid so pixel values between {0,1}
        x = F.relu(self.fc_unflatten(z))
        x = x.view(-1, 512, 4, 4)
        x = F.relu(self.bn1(self.conv_t1(x))) # 4 -> 8
        x = F.relu(self.bn2(self.conv_t2(x))) # 8 -> 16
        x = F.relu(self.bn3(self.conv_t3(x))) # 16 -> 32
        x = F.relu(self.bn4(self.conv_t4(x))) # 32 -> 64
        x = torch.sigmoid(self.conv_t5(x)) # 64 -> 128
        return x

class VAE(nn.Module):
    def __init__(self, latent_dim = 128, in_channels = 3):
        super(VAE, self).__init__()
        self.encoder = VAE_Encoder(latent_dim = latent_dim, in_channels = in_channels)
        self.decoder = VAE_Decoder(latent_dim = latent_dim, out_channels = in_channels)

    def reparameterize(self, mean, logv):
        std = torch.exp(0.5 * logv)
        eps = torch.randn_like(std)
        return mean + eps * std

    def forward(self, x):
        mean, logv = self.encoder(x)
        z = self.reparameterize(mean, logv)
        reconstruction = self.decoder(z)
        return reconstruction, mean, logv