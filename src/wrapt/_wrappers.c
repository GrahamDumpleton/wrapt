/* ------------------------------------------------------------------------- */

/* stable ABI Python >= 3.5 */
#define Py_LIMITED_API 0x03050000

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
    PyObject *weakreflist;
} WraptObjectProxyObject;

static PyTypeObject *WraptObjectProxy_Type;
static PyTypeObject *WraptCallableObjectProxy_Type;

typedef struct {
    WraptObjectProxyObject object_proxy;

    PyObject *args;
    PyObject *kwargs;
} WraptPartialCallableObjectProxyObject;

static PyTypeObject *WraptPartialCallableObjectProxy_Type;

typedef struct {
    WraptObjectProxyObject object_proxy;

    PyObject *instance;
    PyObject *wrapper;
    PyObject *enabled;
    PyObject *binding;
    PyObject *parent;
} WraptFunctionWrapperObject;

static PyTypeObject *WraptFunctionWrapperBase_Type;
static PyTypeObject *WraptBoundFunctionWrapper_Type;
static PyTypeObject *WraptFunctionWrapper_Type;

static PyObject *
type_getname(PyTypeObject *type)
{
    return PyObject_GetAttrString((PyObject *)type, "__name__");
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_new(PyTypeObject *type,
        PyObject *args, PyObject *kwds)
{
    WraptObjectProxyObject *self;
    allocfunc tp_alloc;

    tp_alloc = (allocfunc)PyType_GetSlot(type, Py_tp_alloc);
    self = (WraptObjectProxyObject *)tp_alloc(type, 0);

    if (!self)
        return NULL;

    self->dict = PyDict_New();
    self->wrapped = NULL;
    self->weakreflist = NULL;

    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_raw_init(WraptObjectProxyObject *self,
        PyObject *wrapped)
{
    static PyObject *module_str = NULL;
    static PyObject *doc_str = NULL;

    PyObject *object = NULL;

    Py_INCREF(wrapped);
    Py_XDECREF(self->wrapped);
    self->wrapped = wrapped;

    if (!module_str) {
        module_str = PyUnicode_InternFromString("__module__");
    }

    if (!doc_str) {
        doc_str = PyUnicode_InternFromString("__doc__");
    }

    object = PyObject_GetAttr(wrapped, module_str);

    if (object) {
        if (PyDict_SetItem(self->dict, module_str, object) == -1) {
            Py_DECREF(object);
            return -1;
        }
        Py_DECREF(object);
    }
    else
        PyErr_Clear();

    object = PyObject_GetAttr(wrapped, doc_str);

    if (object) {
        if (PyDict_SetItem(self->dict, doc_str, object) == -1) {
            Py_DECREF(object);
            return -1;
        }
        Py_DECREF(object);
    }
    else
        PyErr_Clear();

    return 0;
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_init(WraptObjectProxyObject *self,
        PyObject *args, PyObject *kwds)
{
    PyObject *wrapped = NULL;

    static char *kwlist[] = { "wrapped", NULL };

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:ObjectProxy",
            kwlist, &wrapped)) {
        return -1;
    }

    return WraptObjectProxy_raw_init(self, wrapped);
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_traverse(WraptObjectProxyObject *self,
        visitproc visit, void *arg)
{
    Py_VISIT(self->dict);
    Py_VISIT(self->wrapped);

    return 0;
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_clear(WraptObjectProxyObject *self)
{
    Py_CLEAR(self->dict);
    Py_CLEAR(self->wrapped);

    return 0;
}

/* ------------------------------------------------------------------------- */

static void WraptObjectProxy_dealloc(WraptObjectProxyObject *self)
{
    PyTypeObject *tp = Py_TYPE(self);

    PyObject_GC_UnTrack(self);

    if (self->weakreflist != NULL)
        PyObject_ClearWeakRefs((PyObject *)self);

    WraptObjectProxy_clear(self);

    freefunc free_func = PyType_GetSlot(Py_TYPE(self), Py_tp_free);
    free_func(self);

    Py_DECREF(tp);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_repr(WraptObjectProxyObject *self)
{
    PyObject *repr = NULL;
    PyObject *sname = NULL;
    PyObject *wname = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    sname = type_getname(Py_TYPE(self));
    if (sname == NULL) {
        return NULL;
    }

    wname = type_getname(Py_TYPE(self->wrapped));
    if (wname == NULL) {
        Py_DECREF(sname);
        return NULL;
    }

    repr = PyUnicode_FromFormat("<%U at %p for %U at %p>",
        sname, self, wname, self->wrapped);
    Py_DECREF(sname);
    Py_DECREF(wname);
    return repr;
}

/* ------------------------------------------------------------------------- */

static Py_hash_t WraptObjectProxy_hash(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return -1;
    }

    return PyObject_Hash(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_str(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyObject_Str(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_add(PyObject *o1, PyObject *o2)
{
    if (PyObject_IsInstance(o1, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o1)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o1 = ((WraptObjectProxyObject *)o1)->wrapped;
    }

    if (PyObject_IsInstance(o2, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o2)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o2 = ((WraptObjectProxyObject *)o2)->wrapped;
    }

    return PyNumber_Add(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_subtract(PyObject *o1, PyObject *o2)
{
    if (PyObject_IsInstance(o1, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o1)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o1 = ((WraptObjectProxyObject *)o1)->wrapped;
    }

    if (PyObject_IsInstance(o2, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o2)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o2 = ((WraptObjectProxyObject *)o2)->wrapped;
    }


    return PyNumber_Subtract(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_multiply(PyObject *o1, PyObject *o2)
{
    if (PyObject_IsInstance(o1, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o1)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o1 = ((WraptObjectProxyObject *)o1)->wrapped;
    }

    if (PyObject_IsInstance(o2, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o2)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o2 = ((WraptObjectProxyObject *)o2)->wrapped;
    }

    return PyNumber_Multiply(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_remainder(PyObject *o1, PyObject *o2)
{
    if (PyObject_IsInstance(o1, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o1)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o1 = ((WraptObjectProxyObject *)o1)->wrapped;
    }

    if (PyObject_IsInstance(o2, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o2)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o2 = ((WraptObjectProxyObject *)o2)->wrapped;
    }

    return PyNumber_Remainder(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_divmod(PyObject *o1, PyObject *o2)
{
    if (PyObject_IsInstance(o1, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o1)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o1 = ((WraptObjectProxyObject *)o1)->wrapped;
    }

    if (PyObject_IsInstance(o2, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o2)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o2 = ((WraptObjectProxyObject *)o2)->wrapped;
    }

    return PyNumber_Divmod(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_power(PyObject *o1, PyObject *o2,
        PyObject *modulo)
{
    if (PyObject_IsInstance(o1, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o1)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o1 = ((WraptObjectProxyObject *)o1)->wrapped;
    }

    if (PyObject_IsInstance(o2, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o2)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o2 = ((WraptObjectProxyObject *)o2)->wrapped;
    }

    return PyNumber_Power(o1, o2, modulo);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_negative(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyNumber_Negative(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_positive(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyNumber_Positive(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_absolute(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyNumber_Absolute(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_bool(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return -1;
    }

    return PyObject_IsTrue(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_invert(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyNumber_Invert(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_lshift(PyObject *o1, PyObject *o2)
{
    if (PyObject_IsInstance(o1, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o1)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o1 = ((WraptObjectProxyObject *)o1)->wrapped;
    }

    if (PyObject_IsInstance(o2, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o2)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o2 = ((WraptObjectProxyObject *)o2)->wrapped;
    }

    return PyNumber_Lshift(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_rshift(PyObject *o1, PyObject *o2)
{
    if (PyObject_IsInstance(o1, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o1)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o1 = ((WraptObjectProxyObject *)o1)->wrapped;
    }

    if (PyObject_IsInstance(o2, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o2)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o2 = ((WraptObjectProxyObject *)o2)->wrapped;
    }

    return PyNumber_Rshift(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_and(PyObject *o1, PyObject *o2)
{
    if (PyObject_IsInstance(o1, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o1)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o1 = ((WraptObjectProxyObject *)o1)->wrapped;
    }

    if (PyObject_IsInstance(o2, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o2)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o2 = ((WraptObjectProxyObject *)o2)->wrapped;
    }

    return PyNumber_And(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_xor(PyObject *o1, PyObject *o2)
{
    if (PyObject_IsInstance(o1, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o1)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o1 = ((WraptObjectProxyObject *)o1)->wrapped;
    }

    if (PyObject_IsInstance(o2, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o2)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o2 = ((WraptObjectProxyObject *)o2)->wrapped;
    }

    return PyNumber_Xor(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_or(PyObject *o1, PyObject *o2)
{
    if (PyObject_IsInstance(o1, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o1)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o1 = ((WraptObjectProxyObject *)o1)->wrapped;
    }

    if (PyObject_IsInstance(o2, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o2)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o2 = ((WraptObjectProxyObject *)o2)->wrapped;
    }

    return PyNumber_Or(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_long(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyNumber_Long(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_float(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyNumber_Float(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_add(WraptObjectProxyObject *self,
        PyObject *other)
{
    PyObject *object = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    if (PyObject_IsInstance(other, (PyObject *)WraptObjectProxy_Type))
        other = ((WraptObjectProxyObject *)other)->wrapped;

    object = PyNumber_InPlaceAdd(self->wrapped, other);

    if (!object)
        return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_subtract(
        WraptObjectProxyObject *self, PyObject *other)
{
    PyObject *object = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    if (PyObject_IsInstance(other, (PyObject *)WraptObjectProxy_Type))
        other = ((WraptObjectProxyObject *)other)->wrapped;

    object = PyNumber_InPlaceSubtract(self->wrapped, other);

    if (!object)
        return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_multiply(
        WraptObjectProxyObject *self, PyObject *other)
{
    PyObject *object = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    if (PyObject_IsInstance(other, (PyObject *)WraptObjectProxy_Type))
        other = ((WraptObjectProxyObject *)other)->wrapped;

    object = PyNumber_InPlaceMultiply(self->wrapped, other);

    if (!object)
        return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_remainder(
        WraptObjectProxyObject *self, PyObject *other)
{
    PyObject *object = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    if (PyObject_IsInstance(other, (PyObject *)WraptObjectProxy_Type))
        other = ((WraptObjectProxyObject *)other)->wrapped;

    object = PyNumber_InPlaceRemainder(self->wrapped, other);

    if (!object)
        return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_power(WraptObjectProxyObject *self,
        PyObject *other, PyObject *modulo)
{
    PyObject *object = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    if (PyObject_IsInstance(other, (PyObject *)WraptObjectProxy_Type))
        other = ((WraptObjectProxyObject *)other)->wrapped;

    object = PyNumber_InPlacePower(self->wrapped, other, modulo);

    if (!object)
        return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_lshift(WraptObjectProxyObject *self,
        PyObject *other)
{
    PyObject *object = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    if (PyObject_IsInstance(other, (PyObject *)WraptObjectProxy_Type))
        other = ((WraptObjectProxyObject *)other)->wrapped;

    object = PyNumber_InPlaceLshift(self->wrapped, other);

    if (!object)
        return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_rshift(WraptObjectProxyObject *self,
        PyObject *other)
{
    PyObject *object = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    if (PyObject_IsInstance(other, (PyObject *)WraptObjectProxy_Type))
        other = ((WraptObjectProxyObject *)other)->wrapped;

    object = PyNumber_InPlaceRshift(self->wrapped, other);

    if (!object)
        return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_and(WraptObjectProxyObject *self,
        PyObject *other)
{
    PyObject *object = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    if (PyObject_IsInstance(other, (PyObject *)WraptObjectProxy_Type))
        other = ((WraptObjectProxyObject *)other)->wrapped;

    object = PyNumber_InPlaceAnd(self->wrapped, other);

    if (!object)
        return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_xor(WraptObjectProxyObject *self,
        PyObject *other)
{
    PyObject *object = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    if (PyObject_IsInstance(other, (PyObject *)WraptObjectProxy_Type))
        other = ((WraptObjectProxyObject *)other)->wrapped;

    object = PyNumber_InPlaceXor(self->wrapped, other);

    if (!object)
        return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_or(WraptObjectProxyObject *self,
        PyObject *other)
{
    PyObject *object = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    if (PyObject_IsInstance(other, (PyObject *)WraptObjectProxy_Type))
        other = ((WraptObjectProxyObject *)other)->wrapped;

    object = PyNumber_InPlaceOr(self->wrapped, other);

    if (!object)
        return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_floor_divide(PyObject *o1, PyObject *o2)
{
    if (PyObject_IsInstance(o1, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o1)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o1 = ((WraptObjectProxyObject *)o1)->wrapped;
    }

    if (PyObject_IsInstance(o2, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o2)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o2 = ((WraptObjectProxyObject *)o2)->wrapped;
    }

    return PyNumber_FloorDivide(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_true_divide(PyObject *o1, PyObject *o2)
{
    if (PyObject_IsInstance(o1, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o1)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o1 = ((WraptObjectProxyObject *)o1)->wrapped;
    }

    if (PyObject_IsInstance(o2, (PyObject *)WraptObjectProxy_Type)) {
        if (!((WraptObjectProxyObject *)o2)->wrapped) {
          PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
          return NULL;
        }

        o2 = ((WraptObjectProxyObject *)o2)->wrapped;
    }

    return PyNumber_TrueDivide(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_floor_divide(
        WraptObjectProxyObject *self, PyObject *other)
{
    PyObject *object = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    if (PyObject_IsInstance(other, (PyObject *)WraptObjectProxy_Type))
        other = ((WraptObjectProxyObject *)other)->wrapped;

    object = PyNumber_InPlaceFloorDivide(self->wrapped, other);

    if (!object)
        return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_true_divide(
        WraptObjectProxyObject *self, PyObject *other)
{
    PyObject *object = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    if (PyObject_IsInstance(other, (PyObject *)WraptObjectProxy_Type))
        other = ((WraptObjectProxyObject *)other)->wrapped;

    object = PyNumber_InPlaceTrueDivide(self->wrapped, other);

    if (!object)
        return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_index(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyNumber_Index(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static Py_ssize_t WraptObjectProxy_length(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return -1;
    }

    return PyObject_Length(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_contains(WraptObjectProxyObject *self,
        PyObject *value)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return -1;
    }

    return PySequence_Contains(self->wrapped, value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_getitem(WraptObjectProxyObject *self,
        PyObject *key)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyObject_GetItem(self->wrapped, key);
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_setitem(WraptObjectProxyObject *self,
        PyObject *key, PyObject* value)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return -1;
    }

    if (value == NULL)
        return PyObject_DelItem(self->wrapped, key);
    else
        return PyObject_SetItem(self->wrapped, key, value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_dir(
        WraptObjectProxyObject *self, PyObject *args)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
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
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    method = PyObject_GetAttrString(self->wrapped, "__enter__");

    if (!method)
        return NULL;

    result = PyObject_Call(method, args, kwds);

    Py_DECREF(method);

    return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_exit(
        WraptObjectProxyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *method = NULL;
    PyObject *result = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    method = PyObject_GetAttrString(self->wrapped, "__exit__");

    if (!method)
        return NULL;

    result = PyObject_Call(method, args, kwds);

    Py_DECREF(method);

    return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_copy(
        WraptObjectProxyObject *self, PyObject *args, PyObject *kwds)
{
    PyErr_SetString(PyExc_NotImplementedError,
                    "object proxy must define __copy__()");

    return NULL;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_deepcopy(
        WraptObjectProxyObject *self, PyObject *args, PyObject *kwds)
{
    PyErr_SetString(PyExc_NotImplementedError,
                    "object proxy must define __deepcopy__()");

    return NULL;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_reduce(
        WraptObjectProxyObject *self, PyObject *args, PyObject *kwds)
{
    PyErr_SetString(PyExc_NotImplementedError,
                    "object proxy must define __reduce_ex__()");

    return NULL;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_reduce_ex(
        WraptObjectProxyObject *self, PyObject *args, PyObject *kwds)
{
    PyErr_SetString(PyExc_NotImplementedError,
                    "object proxy must define __reduce_ex__()");

    return NULL;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_bytes(
        WraptObjectProxyObject *self, PyObject *args)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyObject_Bytes(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_reversed(
        WraptObjectProxyObject *self, PyObject *args)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyObject_CallFunctionObjArgs((PyObject *)&PyReversed_Type,
            self->wrapped, NULL);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_round(
        WraptObjectProxyObject *self, PyObject *args)
{
    PyObject *module = NULL;
    PyObject *dict = NULL;
    PyObject *round = NULL;

    PyObject *result = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    module = PyImport_ImportModule("builtins");

    if (!module)
        return NULL;

    dict = PyModule_GetDict(module);
    round = PyDict_GetItemString(dict, "round");

    if (!round) {
        Py_DECREF(module);
        return NULL;
    }

    Py_INCREF(round);
    Py_DECREF(module);

    result = PyObject_CallFunctionObjArgs(round, self->wrapped, NULL);

    Py_DECREF(round);

    return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_complex(
        WraptObjectProxyObject *self, PyObject *args)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyObject_CallFunctionObjArgs((PyObject *)&PyComplex_Type,
            self->wrapped, NULL);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_mro_entries(
        WraptObjectProxyObject *self, PyObject *args, PyObject *kwds)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return Py_BuildValue("(O)", self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_name(
        WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyObject_GetAttrString(self->wrapped, "__name__");
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_set_name(WraptObjectProxyObject *self,
        PyObject *value)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return -1;
    }

    return PyObject_SetAttrString(self->wrapped, "__name__", value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_qualname(
        WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyObject_GetAttrString(self->wrapped, "__qualname__");
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_set_qualname(WraptObjectProxyObject *self,
        PyObject *value)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return -1;
    }

    return PyObject_SetAttrString(self->wrapped, "__qualname__", value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_module(
        WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyObject_GetAttrString(self->wrapped, "__module__");
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_set_module(WraptObjectProxyObject *self,
        PyObject *value)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return -1;
    }

    if (PyObject_SetAttrString(self->wrapped, "__module__", value) == -1)
        return -1;

    return PyDict_SetItemString(self->dict, "__module__", value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_doc(
        WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyObject_GetAttrString(self->wrapped, "__doc__");
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_set_doc(WraptObjectProxyObject *self,
        PyObject *value)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return -1;
    }

    if (PyObject_SetAttrString(self->wrapped, "__doc__", value) == -1)
        return -1;

    return PyDict_SetItemString(self->dict, "__doc__", value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_class(
        WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyObject_GetAttrString(self->wrapped, "__class__");
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_annotations(
        WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyObject_GetAttrString(self->wrapped, "__annotations__");
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_set_annotations(WraptObjectProxyObject *self,
        PyObject *value)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return -1;
    }

    return PyObject_SetAttrString(self->wrapped, "__annotations__", value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_wrapped(
        WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    Py_INCREF(self->wrapped);
    return self->wrapped;
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_set_wrapped(WraptObjectProxyObject *self,
        PyObject *value)
{
    if (!value) {
        PyErr_SetString(PyExc_TypeError, "__wrapped__ must be an object");
        return -1;
    }

    Py_INCREF(value);
    Py_XDECREF(self->wrapped);

    self->wrapped = value;

    return 0;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_getattro(
        WraptObjectProxyObject *self, PyObject *name)
{
    PyObject *object = NULL;
    PyObject *result = NULL;

    static PyObject *getattr_str = NULL;

    object = PyObject_GenericGetAttr((PyObject *)self, name);

    if (object)
        return object;

    PyErr_Clear();

    if (!getattr_str) {
        getattr_str = PyUnicode_InternFromString("__getattr__");
    }

    object = PyObject_GenericGetAttr((PyObject *)self, getattr_str);

    if (!object)
        return NULL;

    result = PyObject_CallFunctionObjArgs(object, name, NULL);

    Py_DECREF(object);

    return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_getattr(
        WraptObjectProxyObject *self, PyObject *args)
{
    PyObject *name = NULL;

    if (!PyArg_ParseTuple(args, "U:__getattr__", &name))
        return NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyObject_GetAttr(self->wrapped, name);
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_setattro(
        WraptObjectProxyObject *self, PyObject *name, PyObject *value)
{
    static PyObject *self_str = NULL;
    static PyObject *wrapped_str = NULL;
    static PyObject *startswith_str = NULL;

    PyObject *match = NULL;

    if (!startswith_str) {
        startswith_str = PyUnicode_InternFromString("startswith");
    }

    if (!self_str) {
        self_str = PyUnicode_InternFromString("_self_");
    }

    match = PyObject_CallMethodObjArgs(name, startswith_str, self_str, NULL);

    if (match == Py_True) {
        Py_DECREF(match);

        return PyObject_GenericSetAttr((PyObject *)self, name, value);
    }
    else if (!match)
        PyErr_Clear();

    Py_XDECREF(match);

    if (!wrapped_str) {
        wrapped_str = PyUnicode_InternFromString("__wrapped__");
    }

    if (PyObject_HasAttr((PyObject *)Py_TYPE(self), name))
        return PyObject_GenericSetAttr((PyObject *)self, name, value);

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return -1;
    }

    return PyObject_SetAttr(self->wrapped, name, value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_richcompare(WraptObjectProxyObject *self,
        PyObject *other, int opcode)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyObject_RichCompare(self->wrapped, other, opcode);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_iter(WraptObjectProxyObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyObject_GetIter(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyMethodDef WraptObjectProxy_methods[] = {
    { "__dir__",    (PyCFunction)WraptObjectProxy_dir, METH_NOARGS, 0 },
    { "__enter__",  (PyCFunction)WraptObjectProxy_enter,
                    METH_VARARGS | METH_KEYWORDS, 0 },
    { "__exit__",   (PyCFunction)WraptObjectProxy_exit,
                    METH_VARARGS | METH_KEYWORDS, 0 },
    { "__copy__",   (PyCFunction)WraptObjectProxy_copy,
                    METH_NOARGS, 0 },
    { "__deepcopy__", (PyCFunction)WraptObjectProxy_deepcopy,
                    METH_VARARGS | METH_KEYWORDS, 0 },
    { "__reduce__", (PyCFunction)WraptObjectProxy_reduce,
                    METH_NOARGS, 0 },
    { "__reduce_ex__", (PyCFunction)WraptObjectProxy_reduce_ex,
                    METH_VARARGS | METH_KEYWORDS, 0 },
    { "__getattr__", (PyCFunction)WraptObjectProxy_getattr,
                    METH_VARARGS , 0 },
    { "__bytes__",  (PyCFunction)WraptObjectProxy_bytes, METH_NOARGS, 0 },
    { "__reversed__", (PyCFunction)WraptObjectProxy_reversed, METH_NOARGS, 0 },
    { "__round__",  (PyCFunction)WraptObjectProxy_round, METH_NOARGS, 0 },
    { "__complex__",  (PyCFunction)WraptObjectProxy_complex, METH_NOARGS, 0 },
#if PY_MAJOR_VERSION > 3 || (PY_MAJOR_VERSION == 3 && PY_MINOR_VERSION >= 7)
    { "__mro_entries__", (PyCFunction)WraptObjectProxy_mro_entries,
                    METH_VARARGS | METH_KEYWORDS, 0 },
#endif
    { NULL, NULL },
};

static PyGetSetDef WraptObjectProxy_getset[] = {
    { "__name__",           (getter)WraptObjectProxy_get_name,
                            (setter)WraptObjectProxy_set_name, 0 },
    { "__qualname__",       (getter)WraptObjectProxy_get_qualname,
                            (setter)WraptObjectProxy_set_qualname, 0 },
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
    { NULL },
};

static struct PyMemberDef WraptObjectProxy_Type_members[] = {
    {"__weaklistoffset__", T_PYSSIZET, offsetof(WraptObjectProxyObject, weakreflist), READONLY},
    {"__dictoffset__", T_PYSSIZET, offsetof(WraptObjectProxyObject, dict), READONLY},
    {NULL},
};

static PyType_Slot WraptObjectProxy_Type_slots[] = {
    {Py_tp_dealloc, WraptObjectProxy_dealloc},
    {Py_tp_repr, WraptObjectProxy_repr},
    {Py_tp_hash, WraptObjectProxy_hash},
    {Py_tp_str, WraptObjectProxy_str},
    {Py_tp_getattro, WraptObjectProxy_getattro},
    {Py_tp_setattro, WraptObjectProxy_setattro},
    {Py_tp_traverse, WraptObjectProxy_traverse},
    {Py_tp_clear, WraptObjectProxy_clear},
    {Py_tp_richcompare, WraptObjectProxy_richcompare},
    {Py_tp_iter, WraptObjectProxy_iter},
    {Py_tp_methods, WraptObjectProxy_methods},
    {Py_tp_members, WraptObjectProxy_Type_members},
    {Py_tp_getset, WraptObjectProxy_getset},
    {Py_tp_init,  WraptObjectProxy_init},
    {Py_tp_alloc, PyType_GenericAlloc},
    {Py_tp_new, WraptObjectProxy_new},
    {Py_tp_free, PyObject_GC_Del},
    /* as_number */
    {Py_nb_add, WraptObjectProxy_add},
    {Py_nb_subtract, WraptObjectProxy_subtract},
    {Py_nb_multiply, WraptObjectProxy_multiply},
    {Py_nb_remainder, WraptObjectProxy_remainder},
    {Py_nb_divmod, WraptObjectProxy_divmod},
    {Py_nb_power, WraptObjectProxy_power},
    {Py_nb_negative, WraptObjectProxy_negative},
    {Py_nb_positive, WraptObjectProxy_positive},
    {Py_nb_absolute, WraptObjectProxy_absolute},
    {Py_nb_bool, WraptObjectProxy_bool},
    {Py_nb_invert, WraptObjectProxy_invert},
    {Py_nb_lshift, WraptObjectProxy_lshift},
    {Py_nb_rshift, WraptObjectProxy_rshift},
    {Py_nb_and, WraptObjectProxy_and},
    {Py_nb_xor, WraptObjectProxy_xor},
    {Py_nb_or, WraptObjectProxy_or},
    {Py_nb_int, WraptObjectProxy_long},
    {Py_nb_float, WraptObjectProxy_float},
    {Py_nb_inplace_add, WraptObjectProxy_inplace_add},
    {Py_nb_inplace_subtract, WraptObjectProxy_inplace_subtract},
    {Py_nb_inplace_multiply, WraptObjectProxy_inplace_multiply},
    {Py_nb_inplace_remainder, WraptObjectProxy_inplace_remainder},
    {Py_nb_inplace_power, WraptObjectProxy_inplace_power},
    {Py_nb_inplace_lshift, WraptObjectProxy_inplace_lshift},
    {Py_nb_inplace_rshift, WraptObjectProxy_inplace_rshift},
    {Py_nb_inplace_and, WraptObjectProxy_inplace_and},
    {Py_nb_inplace_xor, WraptObjectProxy_inplace_xor},
    {Py_nb_inplace_or, WraptObjectProxy_inplace_or},
    {Py_nb_floor_divide, WraptObjectProxy_floor_divide},
    {Py_nb_true_divide, WraptObjectProxy_true_divide},
    {Py_nb_inplace_floor_divide, WraptObjectProxy_inplace_floor_divide},
    {Py_nb_inplace_true_divide, WraptObjectProxy_inplace_true_divide},
    {Py_nb_index, WraptObjectProxy_index},
    /* as_sequence */
    {Py_sq_length, WraptObjectProxy_length},
    {Py_sq_contains, WraptObjectProxy_contains},
    /* as_mapping */
    {Py_mp_length, WraptObjectProxy_length},
    {Py_mp_subscript, WraptObjectProxy_getitem},
    {Py_mp_ass_subscript, WraptObjectProxy_setitem},
    {0, 0},
};

static PyType_Spec WraptObjectProxy_Type_spec = {
    "ObjectProxy",
    sizeof(WraptObjectProxyObject),
    0,
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    WraptObjectProxy_Type_slots
};

/* ------------------------------------------------------------------------- */

static PyObject *WraptCallableObjectProxy_call(
        WraptObjectProxyObject *self, PyObject *args, PyObject *kwds)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    return PyObject_Call(self->wrapped, args, kwds);
}

/* ------------------------------------------------------------------------- */;

static PyGetSetDef WraptCallableObjectProxy_getset[] = {
    { "__module__",         (getter)WraptObjectProxy_get_module,
                            (setter)WraptObjectProxy_set_module, 0 },
    { "__doc__",            (getter)WraptObjectProxy_get_doc,
                            (setter)WraptObjectProxy_set_doc, 0 },
    { NULL },
};

static PyType_Slot WraptCallableObjectProxy_Type_slots[] = {
    {Py_tp_call, WraptCallableObjectProxy_call},
    {Py_tp_getset, WraptCallableObjectProxy_getset},
    {0, 0},
};

static PyType_Spec WraptCallableObjectProxy_Type_spec = {
    "CallableObjectProxy",
    sizeof(WraptObjectProxyObject),
    0,
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    WraptCallableObjectProxy_Type_slots
};

/* ------------------------------------------------------------------------- */

static PyObject *WraptPartialCallableObjectProxy_new(PyTypeObject *type,
        PyObject *args, PyObject *kwds)
{
    WraptPartialCallableObjectProxyObject *self;

    self = (WraptPartialCallableObjectProxyObject *)WraptObjectProxy_new(type,
            args, kwds);

    if (!self)
        return NULL;

    self->args = NULL;
    self->kwargs = NULL;

    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static int WraptPartialCallableObjectProxy_raw_init(
        WraptPartialCallableObjectProxyObject *self,
        PyObject *wrapped, PyObject *args, PyObject *kwargs)
{
    int result = 0;

    result = WraptObjectProxy_raw_init((WraptObjectProxyObject *)self,
            wrapped);

    if (result == 0) {
        Py_INCREF(args);
        Py_XDECREF(self->args);
        self->args = args;

        Py_XINCREF(kwargs);
        Py_XDECREF(self->kwargs);
        self->kwargs = kwargs;
    }

    return result;
}

/* ------------------------------------------------------------------------- */

static int WraptPartialCallableObjectProxy_init(
        WraptPartialCallableObjectProxyObject *self, PyObject *args,
        PyObject *kwds)
{
    PyObject *wrapped = NULL;
    PyObject *fnargs = NULL;

    int result = 0;

    if (!PyObject_Length(args)) {
        PyErr_SetString(PyExc_TypeError,
                "__init__ of partial needs an argument");
        return -1;
    }

    if (PyObject_Length(args) < 1) {
        PyErr_SetString(PyExc_TypeError,
                "partial type takes at least one argument");
        return -1;
    }

    wrapped = PyTuple_GetItem(args, 0);

    if (!PyCallable_Check(wrapped)) {
        PyErr_SetString(PyExc_TypeError,
                "the first argument must be callable");
        return -1;
    }

    fnargs = PyTuple_GetSlice(args, 1, PyTuple_Size(args));

    if (!fnargs)
        return -1;

    result = WraptPartialCallableObjectProxy_raw_init(self, wrapped,
            fnargs, kwds);

    Py_DECREF(fnargs);

    return result;
}

/* ------------------------------------------------------------------------- */

static int WraptPartialCallableObjectProxy_traverse(
        WraptPartialCallableObjectProxyObject *self,
        visitproc visit, void *arg)
{
    WraptObjectProxy_traverse((WraptObjectProxyObject *)self, visit, arg);

    Py_VISIT(self->args);
    Py_VISIT(self->kwargs);

    return 0;
}

/* ------------------------------------------------------------------------- */

static int WraptPartialCallableObjectProxy_clear(
        WraptPartialCallableObjectProxyObject *self)
{
    WraptObjectProxy_clear((WraptObjectProxyObject *)self);

    Py_CLEAR(self->args);
    Py_CLEAR(self->kwargs);

    return 0;
}

/* ------------------------------------------------------------------------- */

static void WraptPartialCallableObjectProxy_dealloc(
        WraptPartialCallableObjectProxyObject *self)
{
    PyObject_GC_UnTrack(self);

    WraptPartialCallableObjectProxy_clear(self);

    WraptObjectProxy_dealloc((WraptObjectProxyObject *)self);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptPartialCallableObjectProxy_call(
        WraptPartialCallableObjectProxyObject *self, PyObject *args,
        PyObject *kwds)
{
    PyObject *fnargs = NULL;
    PyObject *fnkwargs = NULL;

    PyObject *result = NULL;

    long i;
    long offset;

    if (!self->object_proxy.wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    fnargs = PyTuple_New(PyTuple_Size(self->args)+PyTuple_Size(args));

    for (i=0; i<PyTuple_Size(self->args); i++) {
        PyObject *item;
        item = PyTuple_GetItem(self->args, i);
        Py_INCREF(item);
        PyTuple_SetItem(fnargs, i, item);
    }

    offset = PyTuple_Size(self->args);

    for (i=0; i<PyTuple_Size(args); i++) {
        PyObject *item;
        item = PyTuple_GetItem(args, i);
        Py_INCREF(item);
        PyTuple_SetItem(fnargs, offset+i, item);
    }

    fnkwargs = PyDict_New();

    if (self->kwargs && PyDict_Update(fnkwargs, self->kwargs) == -1) {
        Py_DECREF(fnargs);
        Py_DECREF(fnkwargs);
        return NULL;
    }

    if (kwds && PyDict_Update(fnkwargs, kwds) == -1) {
        Py_DECREF(fnargs);
        Py_DECREF(fnkwargs);
        return NULL;
    }

    result = PyObject_Call(self->object_proxy.wrapped,
           fnargs, fnkwargs);

    Py_DECREF(fnargs);
    Py_DECREF(fnkwargs);

    return result;
}

/* ------------------------------------------------------------------------- */;

static PyGetSetDef WraptPartialCallableObjectProxy_getset[] = {
    { "__module__",         (getter)WraptObjectProxy_get_module,
                            (setter)WraptObjectProxy_set_module, 0 },
    { "__doc__",            (getter)WraptObjectProxy_get_doc,
                            (setter)WraptObjectProxy_set_doc, 0 },
    { NULL },
};

static PyType_Slot WraptPartialCallableObjectProxy_Type_slots[] = {
    {Py_tp_dealloc, WraptPartialCallableObjectProxy_dealloc},
    {Py_tp_call, WraptPartialCallableObjectProxy_call},
    {Py_tp_traverse, WraptPartialCallableObjectProxy_traverse},
    {Py_tp_clear, WraptPartialCallableObjectProxy_clear},
    {Py_tp_getset, WraptPartialCallableObjectProxy_getset},
    {Py_tp_init, WraptPartialCallableObjectProxy_init},
    {Py_tp_new, WraptPartialCallableObjectProxy_new},
    {0, 0},
};

static PyType_Spec WraptPartialCallableObjectProxy_Type_spec = {
    "CallableObjectProxy",
    sizeof(WraptPartialCallableObjectProxyObject),
    0,
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    WraptPartialCallableObjectProxy_Type_slots
};

/* ------------------------------------------------------------------------- */

static PyObject *WraptFunctionWrapperBase_new(PyTypeObject *type,
        PyObject *args, PyObject *kwds)
{
    WraptFunctionWrapperObject *self;

    self = (WraptFunctionWrapperObject *)WraptObjectProxy_new(type,
            args, kwds);

    if (!self)
        return NULL;

    self->instance = NULL;
    self->wrapper = NULL;
    self->enabled = NULL;
    self->binding = NULL;
    self->parent = NULL;

    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static int WraptFunctionWrapperBase_raw_init(WraptFunctionWrapperObject *self,
        PyObject *wrapped, PyObject *instance, PyObject *wrapper,
         PyObject *enabled, PyObject *binding, PyObject *parent)
{
    int result = 0;

    result = WraptObjectProxy_raw_init((WraptObjectProxyObject *)self,
            wrapped);

    if (result == 0) {
        Py_INCREF(instance);
        Py_XDECREF(self->instance);
        self->instance = instance;

        Py_INCREF(wrapper);
        Py_XDECREF(self->wrapper);
        self->wrapper = wrapper;

        Py_INCREF(enabled);
        Py_XDECREF(self->enabled);
        self->enabled = enabled;

        Py_INCREF(binding);
        Py_XDECREF(self->binding);
        self->binding = binding;

        Py_INCREF(parent);
        Py_XDECREF(self->parent);
        self->parent = parent;
    }

    return result;
}

/* ------------------------------------------------------------------------- */

static int WraptFunctionWrapperBase_init(WraptFunctionWrapperObject *self,
        PyObject *args, PyObject *kwds)
{
    PyObject *wrapped = NULL;
    PyObject *instance = NULL;
    PyObject *wrapper = NULL;
    PyObject *enabled = Py_None;
    PyObject *binding = NULL;
    PyObject *parent = Py_None;

    static PyObject *function_str = NULL;

    static char *kwlist[] = { "wrapped", "instance", "wrapper",
            "enabled", "binding", "parent", NULL };

    if (!function_str) {
        function_str = PyUnicode_InternFromString("function");
    }

    if (!PyArg_ParseTupleAndKeywords(args, kwds,
            "OOO|OOO:FunctionWrapperBase", kwlist, &wrapped, &instance,
            &wrapper, &enabled, &binding, &parent)) {
        return -1;
    }

    if (!binding)
        binding = function_str;

    return WraptFunctionWrapperBase_raw_init(self, wrapped, instance, wrapper,
            enabled, binding, parent);
}

/* ------------------------------------------------------------------------- */

static int WraptFunctionWrapperBase_traverse(WraptFunctionWrapperObject *self,
        visitproc visit, void *arg)
{
    WraptObjectProxy_traverse((WraptObjectProxyObject *)self, visit, arg);

    Py_VISIT(self->instance);
    Py_VISIT(self->wrapper);
    Py_VISIT(self->enabled);
    Py_VISIT(self->binding);
    Py_VISIT(self->parent);

    return 0;
}

/* ------------------------------------------------------------------------- */

static int WraptFunctionWrapperBase_clear(WraptFunctionWrapperObject *self)
{
    WraptObjectProxy_clear((WraptObjectProxyObject *)self);

    Py_CLEAR(self->instance);
    Py_CLEAR(self->wrapper);
    Py_CLEAR(self->enabled);
    Py_CLEAR(self->binding);
    Py_CLEAR(self->parent);

    return 0;
}

/* ------------------------------------------------------------------------- */

static void WraptFunctionWrapperBase_dealloc(WraptFunctionWrapperObject *self)
{
    PyObject_GC_UnTrack(self);

    WraptFunctionWrapperBase_clear(self);

    WraptObjectProxy_dealloc((WraptObjectProxyObject *)self);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptFunctionWrapperBase_call(
        WraptFunctionWrapperObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *param_kwds = NULL;

    PyObject *result = NULL;

    static PyObject *function_str = NULL;
    static PyObject *classmethod_str = NULL;

    if (!function_str) {
        function_str = PyUnicode_InternFromString("function");
        classmethod_str = PyUnicode_InternFromString("classmethod");
    }

    if (self->enabled != Py_None) {
        if (PyCallable_Check(self->enabled)) {
            PyObject *object = NULL;

            object = PyObject_CallFunctionObjArgs(self->enabled, NULL);

            if (!object)
                return NULL;

            if (PyObject_Not(object)) {
                Py_DECREF(object);
                return PyObject_Call(self->object_proxy.wrapped, args, kwds);
            }

            Py_DECREF(object);
        }
        else if (PyObject_Not(self->enabled)) {
            return PyObject_Call(self->object_proxy.wrapped, args, kwds);
        }
    }

    if (!kwds) {
        param_kwds = PyDict_New();
        kwds = param_kwds;
    }

    if ((self->instance == Py_None) && (self->binding == function_str ||
            PyObject_RichCompareBool(self->binding, function_str,
            Py_EQ) == 1 || self->binding == classmethod_str ||
            PyObject_RichCompareBool(self->binding, classmethod_str,
            Py_EQ) == 1)) {

        PyObject *instance = NULL;

        instance = PyObject_GetAttrString(self->object_proxy.wrapped,
                "__self__");

        if (instance) {
            result = PyObject_CallFunctionObjArgs(self->wrapper,
                    self->object_proxy.wrapped, instance, args, kwds, NULL);

            Py_XDECREF(param_kwds);

            Py_DECREF(instance);

            return result;
        }
        else
            PyErr_Clear();
    }

    result = PyObject_CallFunctionObjArgs(self->wrapper,
            self->object_proxy.wrapped, self->instance, args, kwds, NULL);

    Py_XDECREF(param_kwds);

    return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptFunctionWrapperBase_descr_get(
        WraptFunctionWrapperObject *self, PyObject *obj, PyObject *type)
{
    PyObject *bound_type = NULL;
    PyObject *descriptor = NULL;
    PyObject *result = NULL;

    static PyObject *bound_type_str = NULL;
    static PyObject *function_str = NULL;

    if (!bound_type_str) {
        bound_type_str = PyUnicode_InternFromString(
                "__bound_function_wrapper__");
    }

    if (!function_str) {
        function_str = PyUnicode_InternFromString("function");
    }

    if (self->parent == Py_None) {
        descrgetfunc descr_get;
        if (PyObject_IsInstance(self->object_proxy.wrapped,
                (PyObject *)&PyType_Type)) {
            Py_INCREF(self);
            return (PyObject *)self;
        }

        descr_get = (descrgetfunc)PyType_GetSlot(
            Py_TYPE(self->object_proxy.wrapped), Py_tp_descr_get);
        if (descr_get == NULL) {
            PyObject *name = type_getname(Py_TYPE(self->object_proxy.wrapped));
            if (name == NULL) {
                return NULL;
            }
            PyErr_Format(PyExc_AttributeError,
                    "'%U' object has no attribute '__get__'",
                    name);
            Py_DECREF(name);
            return NULL;
        }

        descriptor = descr_get(
                self->object_proxy.wrapped, obj, type);

        if (!descriptor)
            return NULL;

        if (Py_TYPE(self) != WraptFunctionWrapper_Type) {
            bound_type = PyObject_GenericGetAttr((PyObject *)self,
                    bound_type_str);

            if (!bound_type)
                PyErr_Clear();
        }

        if (obj == NULL)
            obj = Py_None;

        result = PyObject_CallFunctionObjArgs(bound_type ? bound_type :
                (PyObject *)WraptBoundFunctionWrapper_Type, descriptor,
                obj, self->wrapper, self->enabled, self->binding,
                self, NULL);

        Py_XDECREF(bound_type);
        Py_DECREF(descriptor);

        return result;
    }

    if (self->instance == Py_None && (self->binding == function_str ||
            PyObject_RichCompareBool(self->binding, function_str,
            Py_EQ) == 1)) {

        PyObject *wrapped = NULL;

        static PyObject *wrapped_str = NULL;
        descrgetfunc descr_get;

        if (!wrapped_str) {
            wrapped_str = PyUnicode_InternFromString("__wrapped__");
        }

        wrapped = PyObject_GetAttr(self->parent, wrapped_str);

        if (!wrapped)
            return NULL;

        descr_get = (descrgetfunc)PyType_GetSlot(
            Py_TYPE(wrapped), Py_tp_descr_get);

        if (descr_get == NULL) {
            PyObject *name = type_getname(Py_TYPE(wrapped));
            if (name == NULL) {
                Py_DECREF(wrapped);
                return NULL;
            }
            PyErr_Format(PyExc_AttributeError,
                    "'%U' object has no attribute '__get__'",
                    name);
            Py_DECREF(wrapped);
            Py_DECREF(name);
            return NULL;
        }

        descriptor = descr_get(wrapped, obj, type);

        Py_DECREF(wrapped);

        if (!descriptor)
            return NULL;

        if (Py_TYPE(self->parent) != WraptFunctionWrapper_Type) {
            bound_type = PyObject_GenericGetAttr((PyObject *)self->parent,
                    bound_type_str);

            if (!bound_type)
                PyErr_Clear();
        }

        if (obj == NULL)
            obj = Py_None;

        result = PyObject_CallFunctionObjArgs(bound_type ? bound_type :
                (PyObject *)WraptBoundFunctionWrapper_Type, descriptor,
                obj, self->wrapper, self->enabled, self->binding,
                self->parent, NULL);

        Py_XDECREF(bound_type);
        Py_DECREF(descriptor);

        return result;
    }

    Py_INCREF(self);
    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptFunctionWrapperBase_set_name(
        WraptFunctionWrapperObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *method = NULL;
    PyObject *result = NULL;

    if (!self->object_proxy.wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    method = PyObject_GetAttrString(self->object_proxy.wrapped,
            "__set_name__");

    if (!method) {
        PyErr_Clear();
        Py_INCREF(Py_None);
        return Py_None;
    }

    result = PyObject_Call(method, args, kwds);

    Py_DECREF(method);

    return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptFunctionWrapperBase_subclasscheck(
        WraptFunctionWrapperObject *self, PyObject *args)
{
    PyObject *subclass = NULL;
    PyObject *object = NULL;
    PyObject *result = NULL;

    int check = 0;

    if (!self->object_proxy.wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");
      return NULL;
    }

    if (!PyArg_ParseTuple(args, "O", &subclass))
        return NULL;

    object = PyObject_GetAttrString(subclass, "__wrapped__");

    if (!object)
        PyErr_Clear();

    check = PyObject_IsSubclass(object ? object: subclass,
            self->object_proxy.wrapped);

    Py_XDECREF(object);

    if (check == -1)
        return NULL;

    result = check ? Py_True : Py_False;

    Py_INCREF(result);

    return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptFunctionWrapperBase_get_self_instance(
        WraptFunctionWrapperObject *self, void *closure)
{
    if (!self->instance) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    Py_INCREF(self->instance);
    return self->instance;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptFunctionWrapperBase_get_self_wrapper(
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

static PyObject *WraptFunctionWrapperBase_get_self_enabled(
        WraptFunctionWrapperObject *self, void *closure)
{
    if (!self->enabled) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    Py_INCREF(self->enabled);
    return self->enabled;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptFunctionWrapperBase_get_self_binding(
        WraptFunctionWrapperObject *self, void *closure)
{
    if (!self->binding) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    Py_INCREF(self->binding);
    return self->binding;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptFunctionWrapperBase_get_self_parent(
        WraptFunctionWrapperObject *self, void *closure)
{
    if (!self->parent) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    Py_INCREF(self->parent);
    return self->parent;
}

/* ------------------------------------------------------------------------- */;

static PyMethodDef WraptFunctionWrapperBase_methods[] = {
    { "__set_name__", (PyCFunction)WraptFunctionWrapperBase_set_name,
                    METH_VARARGS | METH_KEYWORDS, 0 },
    { "__subclasscheck__", (PyCFunction)WraptFunctionWrapperBase_subclasscheck,
                    METH_VARARGS, 0 },
    { NULL, NULL },
};

/* ------------------------------------------------------------------------- */;

static PyGetSetDef WraptFunctionWrapperBase_getset[] = {
    { "__module__",         (getter)WraptObjectProxy_get_module,
                            (setter)WraptObjectProxy_set_module, 0 },
    { "__doc__",            (getter)WraptObjectProxy_get_doc,
                            (setter)WraptObjectProxy_set_doc, 0 },
    { "_self_instance",     (getter)WraptFunctionWrapperBase_get_self_instance,
                            NULL, 0 },
    { "_self_wrapper",      (getter)WraptFunctionWrapperBase_get_self_wrapper,
                            NULL, 0 },
    { "_self_enabled",      (getter)WraptFunctionWrapperBase_get_self_enabled,
                            NULL, 0 },
    { "_self_binding",      (getter)WraptFunctionWrapperBase_get_self_binding,
                            NULL, 0 },
    { "_self_parent",       (getter)WraptFunctionWrapperBase_get_self_parent,
                            NULL, 0 },
    { NULL },
};

static PyType_Slot WraptFunctionWrapperBase_Type_slots[] = {
    {Py_tp_dealloc, WraptFunctionWrapperBase_dealloc},
    {Py_tp_call, WraptFunctionWrapperBase_call},
    {Py_tp_traverse, WraptFunctionWrapperBase_traverse},
    {Py_tp_clear, WraptFunctionWrapperBase_clear},
    {Py_tp_methods, WraptFunctionWrapperBase_methods},
    {Py_tp_getset, WraptFunctionWrapperBase_getset},
    {Py_tp_descr_get, WraptFunctionWrapperBase_descr_get},
    {Py_tp_init, WraptFunctionWrapperBase_init},
    {Py_tp_new, WraptFunctionWrapperBase_new},
    {0, 0},
};

static PyType_Spec WraptFunctionWrapperBase_Type_spec = {
    "_FunctionWrapperBase",
    sizeof(WraptFunctionWrapperObject),
    0,
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    WraptFunctionWrapperBase_Type_slots
};

/* ------------------------------------------------------------------------- */

static PyObject *WraptBoundFunctionWrapper_call(
        WraptFunctionWrapperObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *param_args = NULL;
    PyObject *param_kwds = NULL;

    PyObject *wrapped = NULL;
    PyObject *instance = NULL;

    PyObject *result = NULL;

    static PyObject *function_str = NULL;

    if (self->enabled != Py_None) {
        if (PyCallable_Check(self->enabled)) {
            PyObject *object = NULL;

            object = PyObject_CallFunctionObjArgs(self->enabled, NULL);

            if (!object)
                return NULL;

            if (PyObject_Not(object)) {
                Py_DECREF(object);
                return PyObject_Call(self->object_proxy.wrapped, args, kwds);
            }

            Py_DECREF(object);
        }
        else if (PyObject_Not(self->enabled)) {
            return PyObject_Call(self->object_proxy.wrapped, args, kwds);
        }
    }

    if (!function_str) {
        function_str = PyUnicode_InternFromString("function");
    }

    /* 
    * We need to do things different depending on whether we are likely
    * wrapping an instance method vs a static method or class method.
    */

    if (self->binding == function_str || PyObject_RichCompareBool(
                self->binding, function_str, Py_EQ) == 1) {

        if (self->instance == Py_None) {
            /*
             * This situation can occur where someone is calling the
             * instancemethod via the class type and passing the
             * instance as the first argument. We need to shift the args
             * before making the call to the wrapper and effectively
             * bind the instance to the wrapped function using a partial
             * so the wrapper doesn't see anything as being different.
             */

            if (PyTuple_Size(args) == 0) {
                PyErr_SetString(PyExc_TypeError,
                        "missing 1 required positional argument");
                return NULL;
            }

            instance = PyTuple_GetItem(args, 0);

            if (!instance)
                return NULL;

            wrapped = PyObject_CallFunctionObjArgs(
                    (PyObject *)WraptPartialCallableObjectProxy_Type,
                    self->object_proxy.wrapped, instance, NULL);

            if (!wrapped)
                return NULL;

            param_args = PyTuple_GetSlice(args, 1, PyTuple_Size(args));

            if (!param_args) {
                Py_DECREF(wrapped);
                return NULL;
            }

            args = param_args;
        }
        else
            instance = self->instance;

        if (!wrapped) {
            Py_INCREF(self->object_proxy.wrapped);
            wrapped = self->object_proxy.wrapped;
        }

        if (!kwds) {
            param_kwds = PyDict_New();
            kwds = param_kwds;
        }

        result = PyObject_CallFunctionObjArgs(self->wrapper, wrapped,
                instance, args, kwds, NULL);

        Py_XDECREF(param_args);
        Py_XDECREF(param_kwds);
        Py_DECREF(wrapped);

        return result;
    }
    else {
        /*
         * As in this case we would be dealing with a classmethod or
         * staticmethod, then _self_instance will only tell us whether
         * when calling the classmethod or staticmethod they did it via
         * an instance of the class it is bound to and not the case
         * where done by the class type itself. We thus ignore
         * _self_instance and use the __self__ attribute of the bound
         * function instead. For a classmethod, this means instance will
         * be the class type and for a staticmethod it will be None.
         * This is probably the more useful thing we can pass through
         * even though we loose knowledge of whether they were called on
         * the instance vs the class type, as it reflects what they have
         * available in the decoratored function.
         */

        instance = PyObject_GetAttrString(self->object_proxy.wrapped,
                "__self__");

        if (!instance) {
            PyErr_Clear();
            Py_INCREF(Py_None);
            instance = Py_None;
        }

        if (!kwds) {
            param_kwds = PyDict_New();
            kwds = param_kwds;
        }

        result = PyObject_CallFunctionObjArgs(self->wrapper,
                self->object_proxy.wrapped, instance, args, kwds, NULL);

        Py_XDECREF(param_kwds);

        Py_DECREF(instance);

        return result;
    }
}

/* ------------------------------------------------------------------------- */

static PyGetSetDef WraptBoundFunctionWrapper_getset[] = {
    { "__module__",         (getter)WraptObjectProxy_get_module,
                            (setter)WraptObjectProxy_set_module, 0 },
    { "__doc__",            (getter)WraptObjectProxy_get_doc,
                            (setter)WraptObjectProxy_set_doc, 0 },
    { NULL },
};

static PyType_Slot WraptBoundFunctionWrapper_Type_slots[] = {
    {Py_tp_call, WraptBoundFunctionWrapper_call},
    {Py_tp_getset, WraptBoundFunctionWrapper_getset},
    {0, 0},
};

static PyType_Spec WraptBoundFunctionWrapper_Type_spec = {
    "BoundFunctionWrapper",
    sizeof(WraptFunctionWrapperObject),
    0,
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    WraptBoundFunctionWrapper_Type_slots
};

/* ------------------------------------------------------------------------- */

static int WraptFunctionWrapper_init(WraptFunctionWrapperObject *self,
        PyObject *args, PyObject *kwds)
{
    PyObject *wrapped = NULL;
    PyObject *wrapper = NULL;
    PyObject *enabled = Py_None;
    PyObject *binding = NULL;
    PyObject *instance = NULL;

    static PyObject *classmethod_str = NULL;
    static PyObject *staticmethod_str = NULL;
    static PyObject *function_str = NULL;

    int result = 0;

    static char *kwlist[] = { "wrapped", "wrapper", "enabled", NULL };

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|O:FunctionWrapper",
            kwlist, &wrapped, &wrapper, &enabled)) {
        return -1;
    }

    if (!classmethod_str) {
        classmethod_str = PyUnicode_InternFromString("classmethod");
    }

    if (!staticmethod_str) {
        staticmethod_str = PyUnicode_InternFromString("staticmethod");
    }

    if (!function_str) {
        function_str = PyUnicode_InternFromString("function");
    }

/* XXX TODO
    if (PyObject_IsInstance(wrapped, (PyObject *)&PyClassMethod_Type)) {
        binding = classmethod_str;
    }
    else if (PyObject_IsInstance(wrapped, (PyObject *)&PyStaticMethod_Type)) {
        binding = staticmethod_str;
    }
    else
*/
    if ((instance = PyObject_GetAttrString(wrapped, "__self__")) != 0) {
        if (PyObject_IsInstance(instance, (PyObject *)&PyType_Type)) {
            binding = classmethod_str;
        }
        else
            binding = function_str;

        Py_DECREF(instance);
    }
    else {
        PyErr_Clear();

        binding = function_str;
    }

    result = WraptFunctionWrapperBase_raw_init(self, wrapped, Py_None,
            wrapper, enabled, binding, Py_None);

    return result;
}

/* ------------------------------------------------------------------------- */

static PyGetSetDef WraptFunctionWrapper_getset[] = {
    { "__module__",         (getter)WraptObjectProxy_get_module,
                            (setter)WraptObjectProxy_set_module, 0 },
    { "__doc__",            (getter)WraptObjectProxy_get_doc,
                            (setter)WraptObjectProxy_set_doc, 0 },
    { NULL },
};

static PyType_Slot WraptFunctionWrapper_Type_slots[] = {
    {Py_tp_getset, WraptFunctionWrapper_getset},
    {Py_tp_init, WraptFunctionWrapper_init},
    {0, 0},
};

static PyType_Spec WraptFunctionWrapper_Type_spec = {
    "FunctionWrapper",
    sizeof(WraptFunctionWrapperObject),
    0,
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    WraptFunctionWrapper_Type_slots
};

/* ------------------------------------------------------------------------- */

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

static PyTypeObject *
init_type(PyObject *module, PyType_Spec *spec, PyTypeObject *base, const char *attrname)
{
    PyObject *newtype = NULL;
    PyObject *bases = NULL;
    if (base != NULL) {
        bases = PyTuple_Pack(1, (PyObject *)base);
        if (bases == NULL) {
            return NULL;
        }
    }
    newtype = PyType_FromSpecWithBases(
        spec, bases
    );
    Py_XDECREF(bases);
    if (newtype == NULL) {
        return NULL;
    }
    assert(((PyTypeObject *)newtype)->tp_traverse != NULL);

    if (PyModule_AddObject(module, attrname, newtype) < 0) {
        Py_DECREF(newtype);
        return NULL;
    }
    Py_INCREF(newtype);
    return (PyTypeObject *)newtype;
}

static PyObject *
moduleinit(void)
{
    PyObject *module;

    module = PyModule_Create(&moduledef);

    if (module == NULL)
        return NULL;

    WraptObjectProxy_Type = (PyTypeObject *)init_type(
        module,
        &WraptObjectProxy_Type_spec,
        NULL,
        "ObjectProxy"
    );
    if (WraptObjectProxy_Type == NULL)
        return NULL; 

    WraptCallableObjectProxy_Type = (PyTypeObject *)init_type(
        module,
        &WraptCallableObjectProxy_Type_spec,
        WraptObjectProxy_Type,
        "CallableObjectProxy"
    );
    if (WraptCallableObjectProxy_Type == NULL)
        return NULL;

    WraptPartialCallableObjectProxy_Type = (PyTypeObject *)init_type(
        module,
        &WraptPartialCallableObjectProxy_Type_spec,
        WraptObjectProxy_Type,
        "PartialCallableObjectProxy"
    );
    if (WraptPartialCallableObjectProxy_Type == NULL)
        return NULL;

    WraptFunctionWrapperBase_Type = (PyTypeObject *)init_type(
        module,
        &WraptFunctionWrapperBase_Type_spec,
        WraptObjectProxy_Type,
        "_FunctionWrapperBase"
    );
    if (WraptFunctionWrapperBase_Type == NULL)
        return NULL;

    WraptBoundFunctionWrapper_Type = (PyTypeObject *)init_type(
        module,
        &WraptBoundFunctionWrapper_Type_spec,
        WraptFunctionWrapperBase_Type,
        "BoundFunctionWrapper"
    );
    if (WraptBoundFunctionWrapper_Type == NULL)
        return NULL;

    WraptFunctionWrapper_Type = (PyTypeObject *)init_type(
        module,
        &WraptFunctionWrapper_Type_spec,
        WraptFunctionWrapperBase_Type,
        "FunctionWrapper"
    );
    if (WraptFunctionWrapper_Type == NULL)
        return NULL;

    return module;
}

PyMODINIT_FUNC PyInit__wrappers(void)
{
    return moduleinit();
}

/* ------------------------------------------------------------------------- */
