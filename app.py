import streamlit as st
import time
import torch
from torch import nn
import matplotlib.pyplot as plt
from matplotlib import rcParams


def train_and_visualize_loss(lr_D, lr_G, num_epochs, latent_dim):
    # create the data
    X = torch.normal(0.0, 1, (1000, 2))
    A = torch.tensor([[1, 2], [-0.1, 0.5]])
    b = torch.tensor([1, 2])
    data = torch.matmul(X, A) + b

    # scatter the data
    plt.scatter(
        data[:100, 0].detach().numpy(),
        data[:100, 1].detach().numpy()
    )

    # generate the dataloader
    batch_size = 8
    dataset = torch.utils.data.TensorDataset(data)
    dataloader = torch.utils.data.DataLoader(
        dataset,
        batch_size,
        shuffle=True
    )

    Gen = nn.Sequential(
        nn.Linear(in_features=2, out_features=2)
    )

    Disc = nn.Sequential(
        nn.Linear(2, 5),
        nn.Tanh(),
        nn.Linear(5, 3),
        nn.Tanh(),
        nn.Linear(3, 1)
    )

    def update_D(X, Z, nnet_D, nnet_G, loss, trainer_D):
        batch_size = X.shape[0]
        ones = torch.ones((batch_size,), device=X.device)
        zeros = torch.zeros((batch_size,), device=X.device)
        trainer_D.zero_grad()
        real_Y = nnet_D(X)
        synth_X = nnet_G(Z)
        synth_Y = nnet_D(synth_X.detach())
        loss_D = (loss(real_Y, ones.reshape(real_Y.shape)) +
                  loss(synth_Y, zeros.reshape(synth_Y.shape))) / 2
        loss_D.backward()
        trainer_D.step()
        return loss_D

    def update_G(Z, nnet_D, nnet_G, loss, trainer_G):
        batch_size = Z.shape[0]
        ones = torch.ones((batch_size,), device=Z.device)
        trainer_G.zero_grad()
        synth_X = nnet_G(Z)
        synth_Y = nnet_D(synth_X)
        loss_G = loss(synth_Y, ones.reshape(synth_Y.shape))
        loss_G.backward()
        trainer_G.step()
        return loss_G

    def init_params(Discriminator, Generator, lr_D, lr_G):
        loss = nn.BCEWithLogitsLoss(reduction='sum')
        for w in Discriminator.parameters():
            # tensor, mean, std
            nn.init.normal_(w, 0, 0.02)
        for w in Generator.parameters():
            nn.init.normal_(w, 0, 0.02)
        trainer_D = torch.optim.Adam(Discriminator.parameters(), lr=lr_D)
        trainer_G = torch.optim.Adam(Generator.parameters(), lr=lr_G)
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        chart = st.pyplot(fig)
        loss_D = []
        loss_G = []

        return loss, trainer_D, trainer_G, fig, axes, loss_D, loss_G, chart

    def compute_losses(X, net_D, net_G, loss, trainer_D, trainer_G, batch_size, latent_dim, data_iter):
        metrics = [0.0]*3
        for (X,) in data_iter:
            batch_size = X.shape[0]
            Z = torch.normal(0, 1, size=(batch_size, latent_dim))
            metric = [update_D(X, Z, net_D, net_G, loss, trainer_D),
                      update_G(Z, net_D, net_G, loss, trainer_G),
                      batch_size]
            metrics = [sum(i) for i in zip(metric, metrics)]

        return metrics

    def display_gen_dist(net_G, axes, latent_dim, data):
        Z = torch.normal(0, 1, size=(100, latent_dim))
        synth_X = net_G(Z).detach().numpy()
        axes[1].cla()
        axes[1].scatter(data[:, 0], data[:, 1])
        axes[1].scatter(synth_X[:, 0], synth_X[:, 1])
        axes[1].legend(['real', 'generated'])
        axes[1].set_title('Sample generated by Generator')

    def display_losses(metrics, loss_D, loss_G, axes, fig, epoch, chart):
        D = metrics[0]/metrics[2]
        loss_D.append(D.detach())
        G = metrics[1]/metrics[2]
        loss_G.append(G.detach())
        axes[0].plot(range(epoch+1), loss_D, c="blue")
        axes[0].plot(range(epoch+1), loss_G, c="green")
        axes[0].legend(['Discriminator loss', 'Generator loss'])
        axes[0].set_title('Losses of Gen and Disc')
        chart.pyplot(fig)  # 显示图表
        time.sleep(0.1)  # 等待0.1秒以模拟删除和重新绘制图表

        return loss_D, loss_G

    def train(net_D, net_G, data_iter, num_epochs, lr_D, lr_G, latent_dim, data):
        # Start timer
        tik = time.perf_counter()
        # Init variables
        loss, trainer_D, trainer_G, fig, axes, loss_D, loss_G, chart = init_params(
            net_D, net_G, lr_D, lr_G)
        for epoch in range(num_epochs):
            # Train one epoch
            metrics = compute_losses(
                X, net_D, net_G, loss, trainer_D, trainer_G, batch_size, latent_dim, data_iter)
            # Visualize generated examples
            display_gen_dist(net_G, axes, latent_dim, data)
            # Show the losses
            loss_D, loss_G = display_losses(
                metrics, loss_D, loss_G, axes, fig, epoch, chart)
        # End timer
        tok = time.perf_counter()
        # Display stats
        print(f'loss_D {loss_D[-1]}, loss_G {loss_G[-1]}, \
            {(metrics[2]*num_epochs) / (tok-tik):.1f} examples/sec')

    # lr_D, lr_G, latent_dim, num_epochs = 0.05, 0.005, 2, 30
    train(Disc, Gen, dataloader, num_epochs, lr_D,
          lr_G, latent_dim, data[:100].detach().numpy())

st.title('GANs対抗ネットワークトレニンーグ可視化アプリ')
st.markdown(
    '''
    モデル：
    ```python
    Gen = nn.Sequential(nn.Linear(in_features=2, out_features=2))
    Disc = nn.Sequential(
        nn.Linear(2, 5), nn.Tanh(), 
        nn.Linear(5, 3), nn.Tanh(), 
        nn.Linear(3, 1)
        )　
    ```
    '''
)
st.subheader('ハイパーパラメータ設定:')

# 获取用户输入
lr_D = st.text_input('判定モデルの学習率(lr_D):', '0.05')
lr_G = st.text_input('生成モデルの学習率(lr_G):', '0.005')
num_epochs = st.text_input('学習回数(num_epochs):', '30')

# 将输入转换为数值类型
try:
    lr_D = float(lr_D)
    lr_G = float(lr_G)
    num_epochs = int(num_epochs)

    if st.button('トレニンーグ開始'):
        train_and_visualize_loss(lr_D=lr_D, lr_G=lr_G,
                                 num_epochs=num_epochs, latent_dim=2)
        st.markdown('トレニンーグ完了。')
        
except ValueError:
    st.error('Something goes wrong with your input.')







