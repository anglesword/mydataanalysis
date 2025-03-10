import numpy as np

# 使用array函数创建一维数组, dtype的使用：将数组中的元素变为dtype指定的类型, ndim参数的使用：指定要创建数组的维度
def create_array_one_dimension() -> None:
    arr = np.array([1,2,3,4], dtype=float, ndmin=2)
    print(arr)
    print(f"ndim={arr.ndim}, shape={arr.shape}, dtype={arr.dtype}, size={arr.size}")

# 使用array函数创建二维数组
def create_array_two_dimension() -> None:
    arr = np.array([[1,2,3], [4,5,6],[7,8,9]])
    print(arr)
    print(f"ndim={arr.ndim}, shape={arr.shape}, dtype={arr.dtype}, size={arr.size}")

# 使用arrange创建数组：
# np.arrange(start, stop, step, dtype),起始值，终止值，步长
def create_array_arrange() -> None:
    arr = np.arange(10, 20, 0.5)
    print(arr)
    print(f"ndim={arr.ndim}, shape={arr.shape}, dtype={arr.dtype}, size={arr.size}")

# 创建random数组,
# np.random.randint() -> 随机整数数组
# np.random.randn(2, 3) -> 创建一个2行3列的二维数组, 该数组为一个标准的正太分布，方差为0
def create_array_random() -> None:
    arr = np.random.random(size=4)
    print(arr)
    print(f"ndim={arr.ndim}, shape={arr.shape}, dtype={arr.dtype}, size={arr.size}")

# 创建随机数组，指定期望和方差的正态分布
def create_array_random_nd() -> None:
    arr = np.random.normal(loc=2, scale=3, size=5)
    print(arr)
    print(f"ndim={arr.ndim}, shape={arr.shape}, dtype={arr.dtype}, size={arr.size}")

# 创建random二维数组，参数中要指定 行，列
def create_array_random_two_dimension() -> None:
    arr = np.random.random(size=(3, 4))
    print(arr)
    print(f"ndim={arr.ndim}, shape={arr.shape}, dtype={arr.dtype}, size={arr.size}")

def main() -> None:
    create_array_one_dimension()
    create_array_two_dimension()
    create_array_arrange()
    create_array_random()
    create_array_random_nd()
    create_array_random_two_dimension()
    create_array_random_nd()

if __name__ == "__main__":
    main()