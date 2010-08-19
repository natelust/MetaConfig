all: CppOnly

# evil boost
B:=gcc43-mt

CppOnly: CppOnly.o
	g++ -Wall -g -O0 -o $@ $< -L${PYTHON_DIR}/lib -lpython2.5 -L${BOOST_DIR}/lib -lboost_system-${B} \
		-L${PEX_POLICY_DIR}/lib -lpex_policy

CppOnly.o: CppOnly.cc
	g++ -Wall -g -O0 -o $@ -c $< \
		-I$(shell ls -d ${PYTHON_DIR}/include/python2.?/) -I${PEX_POLICY_DIR}/include \
		-I${BOOST_DIR}/include -I${DAF_BASE_DIR}/include -I${UTILS_DIR}/include \
		-I${PEX_EXCEPTIONS_DIR}/include
