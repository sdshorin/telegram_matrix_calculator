
from __future__ import annotations
from sys import stdin
from typing import List
from decimal import Decimal, getcontext

class Matrix:
	def __init__(self, arr) -> None:
		if isinstance(arr, Matrix):
			arr = arr.arr
			self.arr = []
			for line in arr:
				self.arr.append(line.copy())
		elif isinstance(arr, str):
			lines = arr.split("\n")
			self.arr = []
			for line in lines:
				self.arr.append(list(map(int, line.split())))
		else:
			self.arr = []
			for line in arr:
				self.arr.append(line.copy())
		
		if not len(self.arr):
			raise MatrixError(self, self, f"Матрица должна быть не пустая")
		matrix_line_size = len(self.arr[0])
		for line in self.arr:
			if len(line) != matrix_line_size:
				raise MatrixError(self, self, f"Линия {line} должна состоять из {matrix_line_size} элементов")
		
	def copy(self):
		return self.__class__(self.arr)

	def __str__(self) -> str:
		return "\n".join(["\t".join(map(str, line)) for line in self.arr])
	
	def print_pretty(self) -> str:
		return "\n".join(["|" + "  \t".join(map(str, line)) + "|" for line in self.arr])

	def size(self):
		if not len(self.arr):
			return (0, 0)
		return (len(self.arr), len(self.arr[0]))
	
	def __add__(self, other: Matrix):
		if self.size() != other.size():
			raise MatrixError(self, other, "Складывать можно только матрицы одинакового размера!")
		result = self.copy()
		for i in range(len(other.arr)):
			for j in range(len(other.arr[0])):
				result.arr[i][j] += other.arr[i][j]
		return result
	
	def __sub__(self, other: Matrix):
		if self.size() != other.size():
			raise MatrixError(self, other, "Складывать можно только матрицы одинакового размера!")
		result = self.copy()
		for i in range(len(other.arr)):
			for j in range(len(other.arr[0])):
				result.arr[i][j] -= other.arr[i][j]
		return result

	def convert_to_decimal(self):
		self.arr = [[Decimal(i) for i in line] for line in self.arr]

	@staticmethod
	def _matrix_mult(mat_1, mat_2):
		result = []
		for row_n in range(len(mat_1)):
			result.append([])
			for column_n in range(len(mat_2[0])):
				_sum = 0
				for n in range(len(mat_2)):
					_sum += mat_1[row_n][n] * mat_2[n][column_n]
				result[row_n].append(_sum)
		return result

	def __mul__(self, other):
		result = self.copy()
		if isinstance(other, float) or isinstance(other, int):
			for i in range(len(result.arr)):
				for j in range(len(result.arr[0])):
					result.arr[i][j] *= other
		elif isinstance(other, Matrix):
			if self.size()[1] != other.size()[0]:
				raise MatrixError(self, other, "Умножать матрицы можно только если a_m==b_n")
			result.arr = Matrix._matrix_mult(self.arr, other.arr)
	
		return result

	__rmul__ = __mul__

	def __pow__(self, pow):
		if pow == 0:
			return Matrix.create_id_matrix(len(self.arr))
		if pow == 1:
			return self.copy()
		if pow % 2 == 0:
			return (self * self) ** int(pow / 2)
		else:
			return self * (self ** (pow -1))

	def transpose(self):
		if not len(self.arr):
			return self
		transposed = []
		for i in range(len(self.arr[0])):
			transposed.append([])
			for j in range(len(self.arr)):
				transposed[i].append(self.arr[j][i])
		self.arr = transposed
		return self
	
	def get_transposd(self):
		copy = self.copy()
		return copy.transpose()
	
	
	def solve(self, free_coeff: List):
		matrix = self.copy()
		coeff = Matrix([free_coeff]).transpose()
		coeff = matrix.solve_with_line(coeff)
		return coeff.transpose().arr[0]
	
	def inverse(self):
		matrix = self.copy()
		inversed = Matrix.create_id_matrix(len(matrix.arr))
		if not len(matrix.arr) or len(matrix.arr) != len(matrix.arr[0]):
			raise MatrixError(self, Matrix(inversed), "Обратную матрицу можно найти только у квадратной матрицы")
		inversed = matrix.solve_with_line(inversed)
		inversed.round(6)
		return inversed


	
	def solve_with_line(matrix, coeff):
		for i in range(len(matrix.arr)):
			lider_line_num = get_lider_line(matrix.arr, i, i)
			if lider_line_num < 0:
				raise MatrixError(matrix, Matrix(coeff), "Не найден лидирующий элемент")
			if lider_line_num != i:
				matrix.element_premutation_2(lider_line_num, i)
				coeff.element_premutation_2(lider_line_num, i)
				lider_line_num = i
			lider = matrix.arr[i][i]
			matrix.element_premutation_3(lider_line_num, 1/lider)
			coeff.element_premutation_3(lider_line_num, 1/lider)
			for line_num in range(i + 1, len(matrix.arr)):
				if matrix.arr[line_num][i]:
					lamb = -matrix.arr[line_num][i]
					matrix.element_premutation_1(line_num, lider_line_num, lamb)
					coeff.element_premutation_1(line_num, lider_line_num, lamb)
		for i in range(len(matrix.arr) -1, -1, -1):
			for line_num in range(i - 1, -1, -1):
				if matrix.arr[line_num][i]:
					lamb = -matrix.arr[line_num][i]
					matrix.element_premutation_1(line_num, i, lamb)
					coeff.element_premutation_1(line_num, i, lamb)
		return coeff

	@staticmethod
	def print_step(m1: Matrix, m2: Matrix):
		print("-" * 20)
		for i in range(m1.size()[0]):
			print(m1.arr[i], "|", m2.arr[i])
		print("-" * 20)

	def round(self, prec):
		self.arr = [[round(i, prec) for i in line] for line in self.arr]


	def element_premutation_2(self, line_1, line_2):
		self.arr[line_1], self.arr[line_2] = self.arr[line_2], self.arr[line_1]
	def element_premutation_1(self, target_line, source_line, lamb):
		for i in range(len(self.arr[0])):
			self.arr[target_line][i] += lamb * self.arr[source_line][i]
	def element_premutation_3(self, target_line, lamb):
		for i in range(len(self.arr[0])):
			self.arr[target_line][i] *= lamb

	@staticmethod
	def transposed(matrix: Matrix):
		m = matrix.copy()
		return m.transpose()
	
	@classmethod
	def create_id_matrix(cls, size):
		arr = [[0 for _ in range(size)] for __ in range(size)]
		for i in range(size):
			arr[i][i] = 1
		return Matrix(arr)


def get_lider_line(arr, start_line, linder_index):
	for i in range(start_line, len(arr)):
		if arr[start_line][linder_index]:
			return i
	return -1

class MatrixError(BaseException):
	def __init__(self, m_1: Matrix, m_2: Matrix, description_p = ""):
		self.matrix1 = m_1
		self.matrix2 = m_2
		self.description = description_p
	
	def __str__(self) -> str:
		return self.description



# if __name__ == "__main__":
# 	import random

# 	a = Matrix([[2, 1 ,0, 0], [3, 2, 0, 0], [1, 1, 3, 4], [2, -1, 2, 3]])
# 	print(a.inverse() * a)

	# def create_random_matrix(x, y):
	# 	return Matrix([[random.randrange(-10, 50) for _ in range(x)] for _ in range(y)])
	
	# for _ in range(100):
	# 	size = random.randrange(1, 6)
	# 	a = create_random_matrix(size, size)
	# 	print(a.inverse() * a)
