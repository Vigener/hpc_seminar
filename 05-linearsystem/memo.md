# レポート課題
次の行列 A と右辺ベクトル b をもつ連立一次方程式 Ax = b を，BiCG法とBiCGSTAB法で解くプログラムを作りなさい．但し，行列 A はCRS形式で格納すること．
行列サイズ n は任意とする.

```
A = [2 1 0 ... 0
     γ 2 1 0 ... 0
      0 γ 2 1 0 ... 0
      0 ... 0 γ 2 1
      0 ... 0 0 γ 2
    ], 

b = A [1 1 1 ... 1]^T
```

• 行列 A のパラメータ は とする．反復は条件： $||r_k||_2 / ||b||_2 <= 10^{-12}$を満たしたら停止すること．初期解 x 0 はゼロベクトルとする．
• 複数のパラメータ について実験し，反復過程における相対残差 をグラフにプロットするとともに考察を述べなさい．
• プログラムリストも提出すること．プログラミング言語は何を用いてもよい．

## BiCG法のアルゴリズム

$x_0$ is an initial guess,
Compute $\bold{r}_0 = \bold{b} - A \bold{x}_0$,
Choose $\bold{r}^*_0$ such that $(\bold{r}^∗_0 , \bold{r}_0 ) \neq0$,
Set $\bold{p}_0 = \bold{r}_0$ and $\bold{p}^*_0 = \bold{r}^*_0$,
For $k = 0, 1, . . . ,$ until $||\bold{r}_k||_2 ≤ ε_{TOL} ||\bold{b}||_2$ do:
  <!-- 行列ベクトル積 -->
  $\bold{q}_k = A \bold{p}_k , \bold{q}^∗_k = A^H \bold{p}^∗_k ,$ 
  <!-- 内積 -->
  $\alpha_k = \frac{(\bold{r}^*_k, \bold{r}_k)}{(\bold{p}^*_k, \bold{q}_k)}$,
  <!-- ベクトルの定数倍と加算 -->
  $\bold{x}_{k+1} = \bold{x}_k + \alpha_k \bold{p}_k$,
  $\bold{r}_{k+1} = \bold{r}_k - \alpha_k \bold{q}_k$, $\bold{r}^*_{k+1} = \bold{r}^*_k - \overline{\alpha}_k \bold{q}^*_k$,
  <!-- 内積 -->
  $\beta_k = \frac{(\bold{r}^*_{k+1}, \bold{r}_{k+1})}{(\bold{r}^*_k, \bold{r}_k)}$,
  <!-- ベクトルの定数倍と加算 -->
  $\bold{p}_{k+1} = \bold{r}_{k+1} + \beta_k \bold{p}_k$, $\bold{p}^*_{k+1} = \bold{r}^*_{k+1} + \overline{\beta}_k \bold{p}^*_k$,
End For

## BiCGSTAB法のアルゴリズム

$x_0$ is an initial guess,
Compute $\bold{r}_0 = \bold{b} - A \bold{x}_0$,
Choose $\bold{r}^*_0$ such that $(\bold{r}^∗_0 , \bold{r}_0 ) \neq0$,
Set $\bold{p}_0 = \bold{r}_0$ , 
For k = 0, 1, . . . , until $||\bold{r}_k||_2 ≤ ||\bold{b}||_2$ do:
  <!-- 行列ベクトル積 -->
  $\bold{q}_k = A \bold{p}_k$,
  <!-- 内積 -->
  $\alpha_k = \frac{(\bold{r}^*_0, \bold{r}_k)}{(\bold{r}^*_0, \bold{q}_k)}$,
  <!-- ベクトルの定数倍と加算 -->
  $\bold{t}_k = \bold{r}_k - \alpha_k \bold{q}_k$,
  <!-- 行列ベクトル積 -->
  $\bold{s}_k = A \bold{t}_k$,
  <!-- 内積 -->
  $\zeta_k = \frac{(\bold{s}_k, \bold{t}_k)}{(\bold{s}_k, \bold{s}_k)}$,
  $\bold{x}_{k+1} = \bold{x}_k + \alpha_k \bold{p}_k + \zeta_k \bold{t}_k$,
  $\bold{r}_{k+1} = \bold{t}_k - \zeta_k \bold{s}_k$,
  <!-- 内積 -->
  $\beta_k = \frac{\alpha_k}{\zeta_k} \cdot \frac{(\bold{r}^*_0, \bold{r}_{k+1})}{(\bold{r}^*_0, \bold{r}_k)}$,
  <!-- ベクトルの定数倍と加算 -->
  $\bold{p}_{k+1} = \bold{r}_{k+1} + \beta_k (\bold{p}_k - \zeta_k \bold{q}_k)$,
End For


