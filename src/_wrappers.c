/* ------------------------------------------------------------------------- */

#include "Python.h"

#include "structmember.h"

#ifndef PyVarObject_HEAD_INIT
#define PyVarObject_HEAD_INIT(type, size) PyObject_HEAD_INIT(type) size,
#endif

/* ------------------------------------------------------------------------- */

typedef struct {
    PyObject_HEAD
    PyObject *dict;
    PyObject *wrapped;
} WraptObjectProxyObject;

PyTypeObject WraptObjectProxy_Type;

typedef struct {
    WraptObjectProxyObject object_proxy;
    PyObject *wrapper;
    PyObject *params;
    PyObject *bound_type;
} WraptFunctionWrapperObject;

PyTypeObject WraptFunctionWrapper_Type;

typedef struct {
    WraptObjectProxyObject object_proxy;
    PyObject *instance;
    PyObject *wrapper;
    PyObject *params;
} WraptBoundFunctionWrapperObject;

PyTypeObject WraptBoundFunctionWrapper_Type;

typedef struct {
    WraptObjectProxyObject object_proxy;
    PyObject *instance;
    PyObject *wrapper;
    PyObject *params;
} WraptBoundMethodWrapperObject;

PyTypeObject WraptBoundMethodWrapper_Type;

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_new(PyTypeObject *type,
        PyObject *args, PyObject *kwds)
{
    WraptObjectProxyObject *self;

    self = (WraptObjectProxyObject *)type->tp_alloc(type, 0);

    if (!self)
        return NULL;

    self->dict = NULL;
    self->wrapped = NULL;

    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_init(WraptObjectProxyObject *self,
        PyObject *args, PyObject *kwds)
{
    PyObject *wrapped = NULL;

    PyObject *name = NULL;
    PyObject *object = NULL;

    static char *kwlist[] = { "wrapped", NULL };

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:ObjectProxy",
            kwlist, &wrapped)) {
        return -1;
    }

    Py_XDECREF(self->dict);
    Py_XDECREF(self->wrapped);

    self->dict = PyDict_New();

    Py_INCREF(wrapped);

    self->wrapped = wrapped;

    object = PyObject_GetAttrString(wrapped, "__name__");

    if (object) {
#if PY_MAJOR_VERSION >= 3
        name = PyUnicode_FromString("__name__");
#else
        name = PyString_FromString("__name__");
#endif
        PyObject_GenericSetAttr((PyObject *)self, name, object);
        Py_DECREF(name);
        Py_DECREF(object);
    }
    else
        PyErr_Clear();

    object = PyObject_GetAttrString(wrapped, "__qualname__");

    if (object) {
#if PY_MAJOR_VERSION >= 3
        name = PyUnicode_FromString("__qualname__");
#else
        name = PyString_FromString("__qualname__");
#endif
        PyObject_GenericSetAttr((PyObject *)self, name, object);
        Py_DECREF(name);
        Py_DECREF(object);
    }
    else
        PyErr_Clear();

    return 0;
}

/* ------------------------------------------------------------------------- */

static void WraptObjectProxy_dealloc(WraptObjectProxyObject *self)
{
    Py_XDECREF(self->dict);
    Py_XDECREF(self->wrapped);

    Py_TYPE(self)->tp_free(self);
}

/* ------------------------------------------------------------------------- */

static long WraptObjectProxy_hash(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return -1;
    }

    return PyObject_Hash(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_call(
        WraptObjectProxyObject *self, PyObject *args, PyObject *kwds)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyEval_CallObjectWithKeywords(self->wrapped, args, kwds);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_add(WraptObjectProxyObject *self,
        PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_Add(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_subtract(WraptObjectProxyObject *self,
        PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_Subtract(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_multiply(WraptObjectProxyObject *self,
        PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_Multiply(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

#if PY_MAJOR_VERSION < 3
static PyObject *WraptObjectProxy_divide(WraptObjectProxyObject *self,
        PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_Divide(self->wrapped, other);
}
#endif

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_remainder(WraptObjectProxyObject *self,
        PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_Remainder(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_divmod(WraptObjectProxyObject *self,
        PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_Divmod(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_power(WraptObjectProxyObject *self,
        PyObject *other, PyObject *modulo)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_Power(self->wrapped, other, modulo);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_negative(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_Negative(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_positive(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_Positive(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_absolute(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_Absolute(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_bool(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return -1;
    }

    return PyObject_IsTrue(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_invert(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_Invert(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_lshift(WraptObjectProxyObject *self,
        PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_Lshift(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_rshift(WraptObjectProxyObject *self,
        PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_Rshift(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_and(WraptObjectProxyObject *self,
        PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_And(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_xor(WraptObjectProxyObject *self,
        PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_Xor(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_or(WraptObjectProxyObject *self,
        PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_Or(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_int(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_Int(self->wrapped);
}

/* ------------------------------------------------------------------------- */

#if PY_MAJOR_VERSION < 3
static PyObject *WraptObjectProxy_long(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_Long(self->wrapped);
}
#endif

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_float(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_Float(self->wrapped);
}

/* ------------------------------------------------------------------------- */

#if PY_MAJOR_VERSION < 3
static PyObject *WraptObjectProxy_oct(WraptObjectProxyObject *self)
{
    PyNumberMethods *nb;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    if ((nb = self->wrapped->ob_type->tp_as_number) == NULL ||
        nb->nb_oct == NULL) {
        PyErr_SetString(PyExc_TypeError,
                   "oct() argument can't be converted to oct");
        return NULL;
    }

    return (*nb->nb_oct)(self->wrapped);
}
#endif

/* ------------------------------------------------------------------------- */

#if PY_MAJOR_VERSION < 3
static PyObject *WraptObjectProxy_hex(WraptObjectProxyObject *self)
{
    PyNumberMethods *nb;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    if ((nb = self->wrapped->ob_type->tp_as_number) == NULL ||
        nb->nb_hex == NULL) {
        PyErr_SetString(PyExc_TypeError,
                   "hex() argument can't be converted to hex");
        return NULL;
    }

    return (*nb->nb_hex)(self->wrapped);
}
#endif

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_add(WraptObjectProxyObject *self,
        PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_InPlaceAdd(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_subtract(
        WraptObjectProxyObject *self, PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_InPlaceSubtract(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_multiply(
        WraptObjectProxyObject *self, PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_InPlaceMultiply(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

#if PY_MAJOR_VERSION < 3
static PyObject *WraptObjectProxy_inplace_divide(
        WraptObjectProxyObject *self, PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_InPlaceDivide(self->wrapped, other);
}
#endif

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_remainder(
        WraptObjectProxyObject *self, PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_InPlaceRemainder(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_power(WraptObjectProxyObject *self,
        PyObject *other, PyObject *modulo)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_InPlacePower(self->wrapped, other, modulo);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_lshift(WraptObjectProxyObject *self,
        PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_InPlaceLshift(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_rshift(WraptObjectProxyObject *self,
        PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_InPlaceRshift(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_and(WraptObjectProxyObject *self,
        PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_InPlaceAnd(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_xor(WraptObjectProxyObject *self,
        PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_InPlaceXor(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_or(WraptObjectProxyObject *self,
        PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_InPlaceOr(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_floor_divide(WraptObjectProxyObject *self,
        PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_FloorDivide(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_true_divide(WraptObjectProxyObject *self,
        PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_TrueDivide(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_floor_divide(
        WraptObjectProxyObject *self, PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_InPlaceFloorDivide(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_true_divide(
        WraptObjectProxyObject *self, PyObject *other)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_InPlaceTrueDivide(self->wrapped, other);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_index(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyNumber_Index(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_dir(
        WraptObjectProxyObject *self, PyObject *args)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyObject_Dir(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_enter(
        WraptObjectProxyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *method = NULL;
    PyObject *result = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    method = PyObject_GetAttrString(self->wrapped, "__enter__");

    if (!method)
        return NULL;

    result = PyEval_CallObjectWithKeywords(method, args, kwds);

    Py_XDECREF(method);

    return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_exit(
        WraptObjectProxyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *method = NULL;
    PyObject *result = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    method = PyObject_GetAttrString(self->wrapped, "__exit__");

    if (!method)
        return NULL;

    result = PyEval_CallObjectWithKeywords(method, args, kwds);

    Py_XDECREF(method);

    return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_module(
        WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyObject_GetAttrString(self->wrapped, "__module__");
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_set_module(WraptObjectProxyObject *self,
        PyObject *value)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return -1;
    }

    return PyObject_SetAttrString(self->wrapped, "__module__", value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_doc(
        WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyObject_GetAttrString(self->wrapped, "__doc__");
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_set_doc(WraptObjectProxyObject *self,
        PyObject *value)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return -1;
    }

    return PyObject_SetAttrString(self->wrapped, "__doc__", value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_class(
        WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyObject_GetAttrString(self->wrapped, "__class__");
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_wrapped(
        WraptObjectProxyObject *self)
{
    PyObject *result = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    result = PyObject_GetAttrString(self->wrapped, "__wrapped__");

    if (!result) {
        Py_INCREF(self->wrapped);
        result = self->wrapped;
    }

    return result;
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_set_wrapped(WraptObjectProxyObject *self,
        PyObject *value)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return -1;
    }

    return PyObject_SetAttrString(self->wrapped, "__wrapped__", value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_annotations(
        WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyObject_GetAttrString(self->wrapped, "__annotations__");
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_set_annotations(WraptObjectProxyObject *self,
        PyObject *value)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return -1;
    }

    return PyObject_SetAttrString(self->wrapped, "__annotations__", value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_self_wrapped(
        WraptObjectProxyObject *self, void *closure)
{
    if (!self->wrapped) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    Py_INCREF(self->wrapped);
    return self->wrapped;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_getattro(
        WraptObjectProxyObject *self, PyObject *name)
{
    PyObject *object = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    object = PyObject_GenericGetAttr((PyObject *)self, name);

    if (object)
        return object;

    PyErr_Clear();

    return PyObject_GetAttr(self->wrapped, name);
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_setattro(
        WraptObjectProxyObject *self, PyObject *name, PyObject *value)
{
    PyObject *self_prefix = NULL;
    PyObject *attr_name = NULL;
    PyObject *attr_qualname = NULL;

    PyObject *match = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return -1;
    }

#if PY_MAJOR_VERSION >= 3
    self_prefix = PyUnicode_FromString("_self_");
    attr_name = PyUnicode_FromString("__name__");
    attr_qualname = PyUnicode_FromString("__qualname__");
#else
    self_prefix = PyString_FromString("_self_");
    attr_name = PyString_FromString("__name__");
    attr_qualname = PyString_FromString("__qualname__");
#endif

    match = PyEval_CallMethod(name, "startswith", "(O)", self_prefix);

    Py_DECREF(self_prefix);

    if (match == Py_True) {
        Py_DECREF(match);

        return PyObject_GenericSetAttr((PyObject *)self, name, value);
    }

    Py_XDECREF(match);

    if (PyObject_RichCompareBool(name, attr_name, Py_EQ) == 1 ||
            PyObject_RichCompareBool(name, attr_qualname, Py_EQ) == 1) {

        if (PyObject_GenericSetAttr((PyObject *)self, name, value) == -1)
            return -1;

        return PyObject_SetAttr(self->wrapped, name, value);
    }

    return PyObject_SetAttr(self->wrapped, name, value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_richcompare(WraptObjectProxyObject *self,
        PyObject *other, int opcode)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyObject_RichCompare(self->wrapped, other, opcode);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_iter(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyObject_GetIter(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyNumberMethods WraptObjectProxy_as_number = {
    (binaryfunc)WraptObjectProxy_add, /*nb_add*/
    (binaryfunc)WraptObjectProxy_subtract, /*nb_subtract*/
    (binaryfunc)WraptObjectProxy_multiply, /*nb_multiply*/
#if PY_MAJOR_VERSION < 3
    (binaryfunc)WraptObjectProxy_divide, /*nb_divide*/
#endif
    (binaryfunc)WraptObjectProxy_remainder, /*nb_remainder*/
    (binaryfunc)WraptObjectProxy_divmod, /*nb_divmod*/
    (ternaryfunc)WraptObjectProxy_power, /*nb_power*/
    (unaryfunc)WraptObjectProxy_negative, /*nb_negative*/
    (unaryfunc)WraptObjectProxy_positive, /*nb_positive*/
    (unaryfunc)WraptObjectProxy_absolute, /*nb_absolute*/
    (inquiry)WraptObjectProxy_bool, /*nb_nonzero/nb_bool*/
    (unaryfunc)WraptObjectProxy_invert, /*nb_invert*/
    (binaryfunc)WraptObjectProxy_lshift, /*nb_lshift*/
    (binaryfunc)WraptObjectProxy_rshift, /*nb_rshift*/
    (binaryfunc)WraptObjectProxy_and, /*nb_and*/
    (binaryfunc)WraptObjectProxy_xor, /*nb_xor*/
    (binaryfunc)WraptObjectProxy_or, /*nb_or*/
#if PY_MAJOR_VERSION < 3
    0,                      /*nb_coerce*/
#endif
    (unaryfunc)WraptObjectProxy_int, /*nb_int*/
#if PY_MAJOR_VERSION < 3
    (unaryfunc)WraptObjectProxy_long, /*nb_long*/
#else
    0,                      /*nb_long/nb_reserved*/
#endif
    (unaryfunc)WraptObjectProxy_float, /*nb_float*/
#if PY_MAJOR_VERSION < 3
    (unaryfunc)WraptObjectProxy_oct, /*nb_oct*/
    (unaryfunc)WraptObjectProxy_hex, /*nb_hex*/
#endif
    (binaryfunc)WraptObjectProxy_inplace_add, /*nb_inplace_add*/
    (binaryfunc)WraptObjectProxy_inplace_subtract, /*nb_inplace_subtract*/
    (binaryfunc)WraptObjectProxy_inplace_multiply, /*nb_inplace_multiply*/
#if PY_MAJOR_VERSION < 3
    (binaryfunc)WraptObjectProxy_inplace_divide, /*nb_inplace_divide*/
#endif
    (binaryfunc)WraptObjectProxy_inplace_remainder, /*nb_inplace_remainder*/
    (ternaryfunc)WraptObjectProxy_inplace_power, /*nb_inplace_power*/
    (binaryfunc)WraptObjectProxy_inplace_lshift, /*nb_inplace_lshift*/
    (binaryfunc)WraptObjectProxy_inplace_rshift, /*nb_inplace_rshift*/
    (binaryfunc)WraptObjectProxy_inplace_and, /*nb_inplace_and*/
    (binaryfunc)WraptObjectProxy_inplace_xor, /*nb_inplace_xor*/
    (binaryfunc)WraptObjectProxy_inplace_or, /*nb_inplace_or*/
    (binaryfunc)WraptObjectProxy_floor_divide, /*nb_floor_divide*/
    (binaryfunc)WraptObjectProxy_true_divide, /*nb_true_divide*/
    (binaryfunc)WraptObjectProxy_inplace_floor_divide, /*nb_inplace_floor_divide*/
    (binaryfunc)WraptObjectProxy_inplace_true_divide, /*nb_inplace_true_divide*/
    (unaryfunc)WraptObjectProxy_index, /*nb_index*/
};

static PyMethodDef WraptObjectProxy_methods[] = {
    { "__dir__",    (PyCFunction)WraptObjectProxy_dir,  METH_NOARGS, 0 },
    { "__enter__",  (PyCFunction)WraptObjectProxy_enter,
                    METH_VARARGS | METH_KEYWORDS, 0 },
    { "__exit__",   (PyCFunction)WraptObjectProxy_exit,
                    METH_VARARGS | METH_KEYWORDS, 0 },
    { NULL, NULL },
};

static PyGetSetDef WraptObjectProxy_getset[] = {
    { "__module__",         (getter)WraptObjectProxy_get_module,
                            (setter)WraptObjectProxy_set_module, 0 },
    { "__doc__",            (getter)WraptObjectProxy_get_doc,
                            (setter)WraptObjectProxy_set_doc, 0 },
    { "__class__",          (getter)WraptObjectProxy_get_class,
                            NULL, 0 },
    { "__annotations__",    (getter)WraptObjectProxy_get_annotations,
                            (setter)WraptObjectProxy_set_annotations, 0 },
    { "__wrapped__",        (getter)WraptObjectProxy_get_wrapped,
                            (setter)WraptObjectProxy_set_wrapped, 0 },
    { "_self_wrapped",      (getter)WraptObjectProxy_get_self_wrapped,
                            NULL, 0 },
    { NULL },
};

PyTypeObject WraptObjectProxy_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "_wrappers.ObjectProxy", /*tp_name*/
    sizeof(WraptObjectProxyObject), /*tp_basicsize*/
    0,                      /*tp_itemsize*/
    /* methods */
    (destructor)WraptObjectProxy_dealloc, /*tp_dealloc*/
    0,                      /*tp_print*/
    0,                      /*tp_getattr*/
    0,                      /*tp_setattr*/
    0,                      /*tp_compare*/
    0,                      /*tp_repr*/
    &WraptObjectProxy_as_number, /*tp_as_number*/
    0,                      /*tp_as_sequence*/
    0,                      /*tp_as_mapping*/
    (hashfunc)WraptObjectProxy_hash, /*tp_hash*/
    (ternaryfunc)WraptObjectProxy_call, /*tp_call*/
    0,                      /*tp_str*/
    (getattrofunc)WraptObjectProxy_getattro, /*tp_getattro*/
    (setattrofunc)WraptObjectProxy_setattro, /*tp_setattro*/
    0,                      /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT |
    Py_TPFLAGS_BASETYPE,    /*tp_flags*/
    0,                      /*tp_doc*/
    0,                      /*tp_traverse*/
    0,                      /*tp_clear*/
    (richcmpfunc)WraptObjectProxy_richcompare, /*tp_richcompare*/
    0,                      /*tp_weaklistoffset*/
    (getiterfunc)WraptObjectProxy_iter, /*tp_iter*/
    0,                      /*tp_iternext*/
    WraptObjectProxy_methods, /*tp_methods*/
    0,                      /*tp_members*/
    WraptObjectProxy_getset, /*tp_getset*/
    0,                      /*tp_base*/
    0,                      /*tp_dict*/
    0,                      /*tp_descr_get*/
    0,                      /*tp_descr_set*/
    offsetof(WraptObjectProxyObject, dict), /*tp_dictoffset*/
    (initproc)WraptObjectProxy_init, /*tp_init*/
    0,                      /*tp_alloc*/
    WraptObjectProxy_new,  /*tp_new*/
    0,                      /*tp_free*/
    0,                      /*tp_is_gc*/
};

/* ------------------------------------------------------------------------- */

static PyObject *WraptFunctionWrapper_new(PyTypeObject *type,
        PyObject *args, PyObject *kwds)
{
    WraptFunctionWrapperObject *self;

    self = (WraptFunctionWrapperObject *)WraptObjectProxy_new(type,
            args, kwds);

    if (!self)
        return NULL;

    self->wrapper = NULL;
    self->params = NULL;
    self->bound_type = NULL;

    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static int WraptFunctionWrapper_init(WraptFunctionWrapperObject *self,
        PyObject *args, PyObject *kwds)
{
    PyObject *wrapped = NULL;
    PyObject *wrapper = NULL;
    PyObject *params = NULL;

    PyObject *base_args = NULL;
    PyObject *base_kwds = NULL;

    int result = 0;

    static char *kwlist[] = { "wrapped", "wrapper", "params", NULL };

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|O:FunctionWrapper",
            kwlist, &wrapped, &wrapper, &params)) {
        return -1;
    }

    Py_XDECREF(self->wrapper);
    Py_XDECREF(self->params);
    Py_XDECREF(self->bound_type);

    self->wrapper = NULL;
    self->params = NULL;
    self->bound_type = NULL;

    base_args = PyTuple_Pack(1, wrapped);
    base_kwds = PyDict_New();

    result = WraptObjectProxy_init((WraptObjectProxyObject *)self,
            base_args, base_kwds);

    if (result == 0) {
        Py_INCREF(wrapper);
        self->wrapper = wrapper;

        if (params) {
            Py_INCREF(params);
            self->params = params;
        }
        else
            self->params = PyDict_New();

        if (PyObject_IsInstance(wrapped,
                (PyObject *)&PyClassMethod_Type) || PyObject_IsInstance(
                wrapped, (PyObject *)&PyStaticMethod_Type)) {
            Py_INCREF((PyObject *)&WraptBoundFunctionWrapper_Type);
            self->bound_type = (PyObject *)&WraptBoundFunctionWrapper_Type;
        }
        else {
            Py_INCREF((PyObject *)&WraptBoundMethodWrapper_Type);
            self->bound_type = (PyObject *)&WraptBoundMethodWrapper_Type;
        }
    }

    Py_DECREF(base_args);
    Py_DECREF(base_kwds);

    return result;
}

/* ------------------------------------------------------------------------- */

static void WraptFunctionWrapper_dealloc(WraptFunctionWrapperObject *self)
{
    Py_XDECREF(self->wrapper);
    Py_XDECREF(self->params);
    Py_XDECREF(self->bound_type);

    WraptObjectProxy_dealloc((WraptObjectProxyObject *)self);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptFunctionWrapper_call(
        WraptFunctionWrapperObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *call_args = NULL;
    PyObject *param_kwds = NULL;

    PyObject *result = NULL;

    if (!kwds) {
        param_kwds = PyDict_New();
        kwds = param_kwds;
    }

    call_args = PyTuple_Pack(4, self->object_proxy.wrapped, Py_None,
            args, kwds);

    result = PyEval_CallObjectWithKeywords(self->wrapper, call_args,
            self->params);

    Py_DECREF(call_args);
    Py_XDECREF(param_kwds);

    return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptFunctionWrapper_descr_get(
        WraptFunctionWrapperObject *self, PyObject *obj, PyObject *type)
{
    PyObject *descriptor = NULL;
    PyObject *result = NULL;

    descriptor = (Py_TYPE(self->object_proxy.wrapped)->tp_descr_get)(
            self->object_proxy.wrapped, obj, type);

    if (!obj)
        obj = Py_None;
    if (!type)
        type = Py_None;

    if (descriptor) {
        result = PyObject_CallFunction(self->bound_type, "(OOOO)",
                descriptor, obj, self->wrapper, self->params);
    }

    Py_XDECREF(descriptor);

    return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptFunctionWrapper_get_self_wrapper(
        WraptFunctionWrapperObject *self, void *closure)
{
    if (!self->wrapper) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    Py_INCREF(self->wrapper);
    return self->wrapper;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptFunctionWrapper_get_self_params(
        WraptFunctionWrapperObject *self, void *closure)
{
    if (!self->params) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    Py_INCREF(self->params);
    return self->params;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptFunctionWrapper_get_self_bound_type(
        WraptFunctionWrapperObject *self, void *closure)
{
    if (!self->bound_type) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    Py_INCREF(self->bound_type);
    return self->bound_type;
}

/* ------------------------------------------------------------------------- */;

static PyGetSetDef WraptFunctionWrapper_getset[] = {
    { "__module__",         (getter)WraptObjectProxy_get_module,
                            (setter)WraptObjectProxy_set_module, 0 },
    { "__doc__",            (getter)WraptObjectProxy_get_doc,
                            (setter)WraptObjectProxy_set_doc, 0 },
    { "_self_wrapper",      (getter)WraptFunctionWrapper_get_self_wrapper,
                            NULL, 0 },
    { "_self_params",       (getter)WraptFunctionWrapper_get_self_params,
                            NULL, 0 },
    { "_self_bound_type",   (getter)WraptFunctionWrapper_get_self_bound_type,
                            NULL, 0 },
    { NULL },
};

PyTypeObject WraptFunctionWrapper_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "_wrappers.FunctionWrapper", /*tp_name*/
    sizeof(WraptFunctionWrapperObject), /*tp_basicsize*/
    0,                      /*tp_itemsize*/
    /* methods */
    (destructor)WraptFunctionWrapper_dealloc, /*tp_dealloc*/
    0,                      /*tp_print*/
    0,                      /*tp_getattr*/
    0,                      /*tp_setattr*/
    0,                      /*tp_compare*/
    0,                      /*tp_repr*/
    0,                      /*tp_as_number*/
    0,                      /*tp_as_sequence*/
    0,                      /*tp_as_mapping*/
    0,                      /*tp_hash*/
    (ternaryfunc)WraptFunctionWrapper_call, /*tp_call*/
    0,                      /*tp_str*/
    0,                      /*tp_getattro*/
    0,                      /*tp_setattro*/
    0,                      /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT |
    Py_TPFLAGS_BASETYPE,    /*tp_flags*/
    0,                      /*tp_doc*/
    0,                      /*tp_traverse*/
    0,                      /*tp_clear*/
    0,                      /*tp_richcompare*/
    0,                      /*tp_weaklistoffset*/
    0,                      /*tp_iter*/
    0,                      /*tp_iternext*/
    0,                      /*tp_methods*/
    0,                      /*tp_members*/
    WraptFunctionWrapper_getset, /*tp_getset*/
    0,                      /*tp_base*/
    0,                      /*tp_dict*/
    (descrgetfunc)WraptFunctionWrapper_descr_get, /*tp_descr_get*/
    0,                      /*tp_descr_set*/
    0,                      /*tp_dictoffset*/
    (initproc)WraptFunctionWrapper_init, /*tp_init*/
    0,                      /*tp_alloc*/
    WraptFunctionWrapper_new,  /*tp_new*/
    0,                      /*tp_free*/
    0,                      /*tp_is_gc*/
};

/* ------------------------------------------------------------------------- */

static PyObject *WraptBoundFunctionWrapper_new(PyTypeObject *type,
        PyObject *args, PyObject *kwds)
{
    WraptBoundFunctionWrapperObject *self;

    self = (WraptBoundFunctionWrapperObject *)WraptObjectProxy_new(type,
            args, kwds);

    if (!self)
        return NULL;

    self->instance = NULL;
    self->wrapper = NULL;
    self->params = NULL;

    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static int WraptBoundFunctionWrapper_init(
        WraptBoundFunctionWrapperObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *wrapped = NULL;
    PyObject *instance = NULL;
    PyObject *wrapper = NULL;
    PyObject *params = NULL;

    PyObject *base_args = NULL;
    PyObject *base_kwds = NULL;

    int result = 0;

    static char *kwlist[] = { "wrapped", "instance", "wrapper",
        "params", NULL };

    if (!PyArg_ParseTupleAndKeywords(args, kwds,
            "OOO|O:BoundFunctionWrapper", kwlist, &wrapped, &instance,
            &wrapper, &params)) {
        return -1;
    }

    Py_XDECREF(self->instance);
    Py_XDECREF(self->wrapper);
    Py_XDECREF(self->params);

    self->instance = NULL;
    self->wrapper = NULL;
    self->params = NULL;

    base_args = PyTuple_Pack(1, wrapped);
    base_kwds = PyDict_New();

    result = WraptObjectProxy_init((WraptObjectProxyObject *)self,
            base_args, base_kwds);

    if (result == 0) {
        Py_INCREF(instance);
        self->instance = instance;

        Py_INCREF(wrapper);
        self->wrapper = wrapper;

        if (params) {
            Py_INCREF(params);
            self->params = params;
        }
        else
            self->params = PyDict_New();
    }

    Py_DECREF(base_args);
    Py_DECREF(base_kwds);

    return result;
}

/* ------------------------------------------------------------------------- */

static void WraptBoundFunctionWrapper_dealloc(
        WraptBoundFunctionWrapperObject *self)
{
    Py_XDECREF(self->instance);
    Py_XDECREF(self->wrapper);
    Py_XDECREF(self->params);

    WraptObjectProxy_dealloc((WraptObjectProxyObject *)self);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptBoundFunctionWrapper_call(
        WraptBoundFunctionWrapperObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *call_args = NULL;
    PyObject *param_kwds = NULL;

    PyObject *result = NULL;

    if (!kwds) {
        param_kwds = PyDict_New();
        kwds = param_kwds;
    }

    call_args = PyTuple_Pack(4, self->object_proxy.wrapped, self->instance,
            args, kwds);

    result = PyEval_CallObjectWithKeywords(self->wrapper, call_args,
            self->params);

    Py_DECREF(call_args);
    Py_XDECREF(param_kwds);

    return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptBoundFunctionWrapper_get_self_instance(
        WraptBoundFunctionWrapperObject *self, void *closure)
{
    if (!self->instance) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    Py_INCREF(self->instance);
    return self->instance;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptBoundFunctionWrapper_get_self_wrapper(
        WraptBoundFunctionWrapperObject *self, void *closure)
{
    if (!self->wrapper) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    Py_INCREF(self->wrapper);
    return self->wrapper;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptBoundFunctionWrapper_get_self_params(
        WraptBoundFunctionWrapperObject *self, void *closure)
{
    if (!self->params) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    Py_INCREF(self->params);
    return self->params;
}

/* ------------------------------------------------------------------------- */;

static PyGetSetDef WraptBoundFunctionWrapper_getset[] = {
    { "__module__",         (getter)WraptObjectProxy_get_module,
                            (setter)WraptObjectProxy_set_module, 0 },
    { "__doc__",            (getter)WraptObjectProxy_get_doc,
                            (setter)WraptObjectProxy_set_doc, 0 },
    { "_self_instance",     (getter)WraptBoundFunctionWrapper_get_self_instance,
                            NULL, 0 },
    { "_self_wrapper",      (getter)WraptBoundFunctionWrapper_get_self_wrapper,
                            NULL, 0 },
    { "_self_params",       (getter)WraptBoundFunctionWrapper_get_self_params,
                            NULL, 0 },
    { NULL },
};

PyTypeObject WraptBoundFunctionWrapper_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "_wrappers.BoundFunctionWrapper", /*tp_name*/
    sizeof(WraptBoundFunctionWrapperObject), /*tp_basicsize*/
    0,                      /*tp_itemsize*/
    /* methods */
    (destructor)WraptBoundFunctionWrapper_dealloc, /*tp_dealloc*/
    0,                      /*tp_print*/
    0,                      /*tp_getattr*/
    0,                      /*tp_setattr*/
    0,                      /*tp_compare*/
    0,                      /*tp_repr*/
    0,                      /*tp_as_number*/
    0,                      /*tp_as_sequence*/
    0,                      /*tp_as_mapping*/
    0,                      /*tp_hash*/
    (ternaryfunc)WraptBoundFunctionWrapper_call, /*tp_call*/
    0,                      /*tp_str*/
    0,                      /*tp_getattro*/
    0,                      /*tp_setattro*/
    0,                      /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT |
    Py_TPFLAGS_BASETYPE,    /*tp_flags*/
    0,                      /*tp_doc*/
    0,                      /*tp_traverse*/
    0,                      /*tp_clear*/
    0,                      /*tp_richcompare*/
    0,                      /*tp_weaklistoffset*/
    0,                      /*tp_iter*/
    0,                      /*tp_iternext*/
    0,                      /*tp_methods*/
    0,                      /*tp_members*/
    WraptBoundFunctionWrapper_getset, /*tp_getset*/
    0,                      /*tp_base*/
    0,                      /*tp_dict*/
    0,                      /*tp_descr_get*/
    0,                      /*tp_descr_set*/
    0,                      /*tp_dictoffset*/
    (initproc)WraptBoundFunctionWrapper_init, /*tp_init*/
    0,                      /*tp_alloc*/
    WraptBoundFunctionWrapper_new, /*tp_new*/
    0,                      /*tp_free*/
    0,                      /*tp_is_gc*/
};

/* ------------------------------------------------------------------------- */

static PyObject *WraptBoundMethodWrapper_new(PyTypeObject *type,
        PyObject *args, PyObject *kwds)
{
    WraptBoundMethodWrapperObject *self;

    self = (WraptBoundMethodWrapperObject *)WraptObjectProxy_new(type,
            args, kwds);

    if (!self)
        return NULL;

    self->instance = NULL;
    self->wrapper = NULL;
    self->params = NULL;

    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static int WraptBoundMethodWrapper_init(
        WraptBoundMethodWrapperObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *wrapped = NULL;
    PyObject *instance = NULL;
    PyObject *wrapper = NULL;
    PyObject *params = NULL;

    PyObject *base_args = NULL;
    PyObject *base_kwds = NULL;

    int result = 0;

    static char *kwlist[] = { "wrapped", "instance", "wrapper",
        "params", NULL };

    if (!PyArg_ParseTupleAndKeywords(args, kwds,
            "OOO|O:BoundMethodWrapper", kwlist, &wrapped, &instance,
            &wrapper, &params)) {
        return -1;
    }

    Py_XDECREF(self->instance);
    Py_XDECREF(self->wrapper);
    Py_XDECREF(self->params);

    self->instance = NULL;
    self->wrapper = NULL;
    self->params = NULL;

    base_args = PyTuple_Pack(1, wrapped);
    base_kwds = PyDict_New();

    result = WraptObjectProxy_init((WraptObjectProxyObject *)self,
            base_args, base_kwds);

    if (result == 0) {
        Py_INCREF(instance);
        self->instance = instance;

        Py_INCREF(wrapper);
        self->wrapper = wrapper;

        if (params) {
            Py_INCREF(params);
            self->params = params;
        }
        else
            self->params = PyDict_New();
    }

    Py_DECREF(base_args);
    Py_DECREF(base_kwds);

    return result;
}

/* ------------------------------------------------------------------------- */

static void WraptBoundMethodWrapper_dealloc(
        WraptBoundMethodWrapperObject *self)
{
    Py_XDECREF(self->instance);
    Py_XDECREF(self->wrapper);
    Py_XDECREF(self->params);

    WraptObjectProxy_dealloc((WraptObjectProxyObject *)self);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptBoundMethodWrapper_call(
        WraptBoundMethodWrapperObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *call_args = NULL;
    PyObject *param_args = NULL;
    PyObject *param_kwds = NULL;

    PyObject *wrapped = NULL;
    PyObject *instance = NULL;

    PyObject *result = NULL;

    if (self->instance == Py_None) {
        PyObject *module = NULL;
        PyObject *partial = NULL;
        PyObject *object = NULL;

        module = PyImport_ImportModule("functools");

        if (module) {
            PyObject *dict = NULL;

            dict = PyModule_GetDict(module);
            partial = PyDict_GetItemString(dict, "partial");

            Py_DECREF(module);
        }

        if (!partial)
            return NULL;

        instance = PyTuple_GetItem(args, 0);

        if (!instance)
            return NULL;

        object = PyObject_CallFunction(partial, "(OO)",
                self->object_proxy.wrapped, instance);

        if (object) {
            Py_INCREF(object);
            wrapped = object;
        }
        else
            return NULL;

        param_args = PyTuple_GetSlice(args, 1, PyTuple_Size(args));
        if (!param_args)
            return NULL;
        args = param_args;
    }
    else
        instance = self->instance;

    if (!kwds) {
        param_kwds = PyDict_New();
        kwds = param_kwds;
    }

    if (!wrapped) {
        call_args = PyTuple_Pack(4, self->object_proxy.wrapped, instance,
                args, kwds);
    }
    else
        call_args = PyTuple_Pack(4, wrapped, instance, args, kwds);

    result = PyEval_CallObjectWithKeywords(self->wrapper, call_args,
            self->params);

    Py_DECREF(call_args);
    Py_XDECREF(param_args);
    Py_XDECREF(param_kwds);
    Py_XDECREF(wrapped);

    return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptBoundMethodWrapper_get_self_instance(
        WraptBoundMethodWrapperObject *self, void *closure)
{
    if (!self->instance) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    Py_INCREF(self->instance);
    return self->instance;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptBoundMethodWrapper_get_self_wrapper(
        WraptBoundMethodWrapperObject *self, void *closure)
{
    if (!self->wrapper) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    Py_INCREF(self->wrapper);
    return self->wrapper;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptBoundMethodWrapper_get_self_params(
        WraptBoundMethodWrapperObject *self, void *closure)
{
    if (!self->params) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    Py_INCREF(self->params);
    return self->params;
}

/* ------------------------------------------------------------------------- */;

static PyGetSetDef WraptBoundMethodWrapper_getset[] = {
    { "__module__",         (getter)WraptObjectProxy_get_module,
                            (setter)WraptObjectProxy_set_module, 0 },
    { "__doc__",            (getter)WraptObjectProxy_get_doc,
                            (setter)WraptObjectProxy_set_doc, 0 },
    { "_self_instance",     (getter)WraptBoundMethodWrapper_get_self_instance,
                            NULL, 0 },
    { "_self_wrapper",      (getter)WraptBoundMethodWrapper_get_self_wrapper,
                            NULL, 0 },
    { "_self_params",       (getter)WraptBoundMethodWrapper_get_self_params,
                            NULL, 0 },
    { NULL },
};

PyTypeObject WraptBoundMethodWrapper_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "_wrappers.BoundMethodWrapper", /*tp_name*/
    sizeof(WraptBoundMethodWrapperObject), /*tp_basicsize*/
    0,                      /*tp_itemsize*/
    /* methods */
    (destructor)WraptBoundMethodWrapper_dealloc, /*tp_dealloc*/
    0,                      /*tp_print*/
    0,                      /*tp_getattr*/
    0,                      /*tp_setattr*/
    0,                      /*tp_compare*/
    0,                      /*tp_repr*/
    0,                      /*tp_as_number*/
    0,                      /*tp_as_sequence*/
    0,                      /*tp_as_mapping*/
    0,                      /*tp_hash*/
    (ternaryfunc)WraptBoundMethodWrapper_call, /*tp_call*/
    0,                      /*tp_str*/
    0,                      /*tp_getattro*/
    0,                      /*tp_setattro*/
    0,                      /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT |
    Py_TPFLAGS_BASETYPE,    /*tp_flags*/
    0,                      /*tp_doc*/
    0,                      /*tp_traverse*/
    0,                      /*tp_clear*/
    0,                      /*tp_richcompare*/
    0,                      /*tp_weaklistoffset*/
    0,                      /*tp_iter*/
    0,                      /*tp_iternext*/
    0,                      /*tp_methods*/
    0,                      /*tp_members*/
    WraptBoundMethodWrapper_getset, /*tp_getset*/
    0,                      /*tp_base*/
    0,                      /*tp_dict*/
    0,                      /*tp_descr_get*/
    0,                      /*tp_descr_set*/
    0,                      /*tp_dictoffset*/
    (initproc)WraptBoundMethodWrapper_init, /*tp_init*/
    0,                      /*tp_alloc*/
    WraptBoundMethodWrapper_new, /*tp_new*/
    0,                      /*tp_free*/
    0,                      /*tp_is_gc*/
};

/* ------------------------------------------------------------------------- */;

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "_wrappers",         /* m_name */
    NULL,                /* m_doc */
    -1,                  /* m_size */
    NULL,                /* m_methods */
    NULL,                /* m_reload */
    NULL,                /* m_traverse */
    NULL,                /* m_clear */
    NULL,                /* m_free */
};
#endif

static PyObject *
moduleinit(void)
{
    PyObject *module;

#if PY_MAJOR_VERSION >= 3
    module = PyModule_Create(&moduledef);
#else
    module = Py_InitModule3("_wrappers", NULL, NULL);
#endif

    if (module == NULL)
        return NULL;

    if (PyType_Ready(&WraptObjectProxy_Type) < 0)
        return NULL;

    /* Ensure that inheritence relationships specified. */

    WraptFunctionWrapper_Type.tp_base = &WraptObjectProxy_Type;
    WraptBoundFunctionWrapper_Type.tp_base = &WraptObjectProxy_Type;
    WraptBoundMethodWrapper_Type.tp_base = &WraptObjectProxy_Type;

    if (PyType_Ready(&WraptFunctionWrapper_Type) < 0)
        return NULL;
    if (PyType_Ready(&WraptBoundFunctionWrapper_Type) < 0)
        return NULL;
    if (PyType_Ready(&WraptBoundMethodWrapper_Type) < 0)
        return NULL;

    Py_INCREF(&WraptObjectProxy_Type);
    PyModule_AddObject(module, "ObjectProxy",
            (PyObject *)&WraptObjectProxy_Type);
    Py_INCREF(&WraptFunctionWrapper_Type);
    PyModule_AddObject(module, "FunctionWrapper",
            (PyObject *)&WraptFunctionWrapper_Type);

    return module;
}

#if PY_MAJOR_VERSION < 3
PyMODINIT_FUNC init_wrappers(void)
{
    moduleinit();
}
#else
PyMODINIT_FUNC PyInit__wrappers(void)
{
    return moduleinit();
}
#endif

/* ------------------------------------------------------------------------- */
