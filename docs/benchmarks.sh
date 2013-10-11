#!/bin/sh

echo "\$ python -m timeit -s 'import benchmarks' 'benchmarks.function3()'"
python -m timeit -s 'import benchmarks' 'benchmarks.function3()'
echo
sleep 5

echo "\$ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3()'"
python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3()'
echo
sleep 5

echo "\$ python -m timeit -s 'import benchmarks' 'benchmarks.Class.function3cmo()'"
python -m timeit -s 'import benchmarks' 'benchmarks.Class.function3cmo()'
echo
sleep 5

echo "\$ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3cmo()'"
python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3cmo()'
echo
sleep 5

echo "\$ python -m timeit -s 'import benchmarks' 'benchmarks.Class.function3cmi()'"
python -m timeit -s 'import benchmarks' 'benchmarks.Class.function3cmi()'
echo
sleep 5

echo "\$ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3cmi()'"
python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3cmi()'
echo
sleep 5

echo "\$ python -m timeit -s 'import benchmarks' 'benchmarks.Class.function3smo()'"
python -m timeit -s 'import benchmarks' 'benchmarks.Class.function3smo()'
echo
sleep 5

echo "\$ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3smo()'"
python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3smo()'
echo
sleep 5

echo "\$ python -m timeit -s 'import benchmarks' 'benchmarks.Class.function3smi()'"
python -m timeit -s 'import benchmarks' 'benchmarks.Class.function3smi()'
echo
sleep 5

echo "\$ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3smi()'"
python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3smi()'
echo
