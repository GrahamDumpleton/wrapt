/* ------------------------------------------------------------------------- */

#include "Python.h"

#include "structmember.h"

#ifndef PyVarObject_HEAD_INIT
#define PyVarObject_HEAD_INIT(type, size) PyObject_HEAD_INIT(type) size,
#endif

/* ------------------------------------------------------------------------- */

typedef struct
{
  PyObject_HEAD

      PyObject *dict;
  PyObject *wrapped;
  PyObject *weakreflist;
} WraptObjectProxyObject;

PyTypeObject WraptObjectProxy_Type;
PyTypeObject WraptCallableObjectProxy_Type;

typedef struct
{
  WraptObjectProxyObject object_proxy;

  PyObject *args;
  PyObject *kwargs;
} WraptPartialCallableObjectProxyObject;

PyTypeObject WraptPartialCallableObjectProxy_Type;

typedef struct
{
  WraptObjectProxyObject object_proxy;

  PyObject *instance;
  PyObject *wrapper;
  PyObject *enabled;
  PyObject *binding;
  PyObject *parent;
  PyObject *owner;
} WraptFunctionWrapperObject;

PyTypeObject WraptFunctionWrapperBase_Type;
PyTypeObject WraptBoundFunctionWrapper_Type;
PyTypeObject WraptFunctionWrapper_Type;

/* ------------------------------------------------------------------------- */

static int raise_uninitialized_wrapper_error(WraptObjectProxyObject *object)
{
  // Before raising an exception we need to first check whether this is a lazy
  // proxy object and attempt to intialize the wrapped object using the supplied
  // callback if so. If the callback is not present then we can proceed to raise
  // the exception, but if the callback is present and returns a value, we set
  // that as the wrapped object and continue and return without raising an error.

  static PyObject *wrapped_str = NULL;
  static PyObject *wrapped_factory_str = NULL;
  static PyObject *wrapped_get_str = NULL;

  PyObject *callback = NULL;
  PyObject *value = NULL;

  if (!wrapped_str)
  {
    wrapped_str = PyUnicode_InternFromString("__wrapped__");
    wrapped_factory_str = PyUnicode_InternFromString("__wrapped_factory__");
    wrapped_get_str = PyUnicode_InternFromString("__wrapped_get__");
  }

  // Note that we use existance of __wrapped_factory__ to gate whether we can
  // attempt to initialize the wrapped object lazily, but it is __wrapped_get__
  // that we actually call to do the initialization. This is so that we can
  // handle multithreading correctly by having __wrapped_get__ use a lock to
  // protect against multiple threads trying to initialize the wrapped object
  // at the same time.

  callback = PyObject_GenericGetAttr((PyObject *)object, wrapped_factory_str);

  if (callback)
  {
    if (callback != Py_None)
    {
      Py_DECREF(callback);

      callback = PyObject_GenericGetAttr((PyObject *)object, wrapped_get_str);

      if (!callback)
        return -1;

      value = PyObject_CallObject(callback, NULL);

      Py_DECREF(callback);

      if (value)
      {
        // We use setattr so that special dunder methods will be properly set.

        if (PyObject_SetAttr((PyObject *)object, wrapped_str, value) == -1)
        {
          Py_DECREF(value);
          return -1;
        }

        Py_DECREF(value);

        return 0;
      }
      else
      {
        return -1;
      }
    }
    else
    {
      Py_DECREF(callback);
    }
  }
  else
    PyErr_Clear();

  // We need to reach into the wrapt.wrappers module to get the exception
  // class because the exception we need to raise needs to inherit from both
  // ValueError and AttributeError and we can't do that in C code using the
  // built in exception classes, or at least not easily or safely.

  PyObject *wrapt_wrappers_module = NULL;
  PyObject *wrapper_not_initialized_error = NULL;

  // Import the wrapt.wrappers module and get the exception class.
  // We do this fresh each time to be safe with multiple sub-interpreters.

  wrapt_wrappers_module = PyImport_ImportModule("wrapt.wrappers");

  if (!wrapt_wrappers_module)
  {
    // Fallback to ValueError if import fails.

    PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");

    return -1;
  }

  wrapper_not_initialized_error = PyObject_GetAttrString(
      wrapt_wrappers_module, "WrapperNotInitializedError");

  if (!wrapper_not_initialized_error)
  {
    // Fallback to ValueError if attribute lookup fails.

    Py_DECREF(wrapt_wrappers_module);

    PyErr_SetString(PyExc_ValueError, "wrapper has not been initialized");

    return -1;
  }

  // Raise the custom exception.

  PyErr_SetString(wrapper_not_initialized_error,
                  "wrapper has not been initialized");

  // Clean up references.

  Py_DECREF(wrapper_not_initialized_error);
  Py_DECREF(wrapt_wrappers_module);

  return -1;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_new(PyTypeObject *type, PyObject *args,
                                      PyObject *kwds)
{
  WraptObjectProxyObject *self;

  self = (WraptObjectProxyObject *)type->tp_alloc(type, 0);

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
  static PyObject *wrapped_factory_str = NULL;

  PyObject *object = NULL;

  // If wrapped is Py_None and we have a __wrapped_factory__ attribute
  // then we defer initialization of the wrapped object until it is first needed.

  if (!wrapped_factory_str)
  {
    wrapped_factory_str = PyUnicode_InternFromString("__wrapped_factory__");
  }

  if (wrapped == Py_None)
  {
    PyObject *callback = NULL;

    callback = PyObject_GenericGetAttr((PyObject *)self, wrapped_factory_str);

    if (callback)
    {
      if (callback != Py_None)
      {
        Py_DECREF(callback);
        return 0;
      }
      else
      {
        Py_DECREF(callback);
      }
    }
    else
      PyErr_Clear();
  }

  Py_INCREF(wrapped);
  Py_XDECREF(self->wrapped);
  self->wrapped = wrapped;

  if (!module_str)
  {
    module_str = PyUnicode_InternFromString("__module__");
  }

  if (!doc_str)
  {
    doc_str = PyUnicode_InternFromString("__doc__");
  }

  object = PyObject_GetAttr(wrapped, module_str);

  if (object)
  {
    if (PyDict_SetItem(self->dict, module_str, object) == -1)
    {
      Py_DECREF(object);
      return -1;
    }
    Py_DECREF(object);
  }
  else
    PyErr_Clear();

  object = PyObject_GetAttr(wrapped, doc_str);

  if (object)
  {
    if (PyDict_SetItem(self->dict, doc_str, object) == -1)
    {
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

static int WraptObjectProxy_init(WraptObjectProxyObject *self, PyObject *args,
                                 PyObject *kwds)
{
  PyObject *wrapped = NULL;

  char *const kwlist[] = {"wrapped", NULL};

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:ObjectProxy", kwlist,
                                   &wrapped))
  {
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
  PyObject_GC_UnTrack(self);

  if (self->weakreflist != NULL)
    PyObject_ClearWeakRefs((PyObject *)self);

  WraptObjectProxy_clear(self);

  Py_TYPE(self)->tp_free(self);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_repr(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyUnicode_FromFormat("<%s at %p for %s at %p>", Py_TYPE(self)->tp_name,
                              self, Py_TYPE(self->wrapped)->tp_name,
                              self->wrapped);
}

/* ------------------------------------------------------------------------- */

static Py_hash_t WraptObjectProxy_hash(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return -1;
  }

  return PyObject_Hash(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_str(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyObject_Str(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_add(PyObject *o1, PyObject *o2)
{
  if (PyObject_IsInstance(o1, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o1)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o1) == -1)
        return NULL;
    }

    o1 = ((WraptObjectProxyObject *)o1)->wrapped;
  }

  if (PyObject_IsInstance(o2, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o2)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o2) == -1)
        return NULL;
    }

    o2 = ((WraptObjectProxyObject *)o2)->wrapped;
  }

  return PyNumber_Add(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_subtract(PyObject *o1, PyObject *o2)
{
  if (PyObject_IsInstance(o1, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o1)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o1) == -1)
        return NULL;
    }

    o1 = ((WraptObjectProxyObject *)o1)->wrapped;
  }

  if (PyObject_IsInstance(o2, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o2)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o2) == -1)
        return NULL;
    }

    o2 = ((WraptObjectProxyObject *)o2)->wrapped;
  }

  return PyNumber_Subtract(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_multiply(PyObject *o1, PyObject *o2)
{
  if (PyObject_IsInstance(o1, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o1)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o1) == -1)
        return NULL;
    }

    o1 = ((WraptObjectProxyObject *)o1)->wrapped;
  }

  if (PyObject_IsInstance(o2, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o2)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o2) == -1)
        return NULL;
    }

    o2 = ((WraptObjectProxyObject *)o2)->wrapped;
  }

  return PyNumber_Multiply(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_remainder(PyObject *o1, PyObject *o2)
{
  if (PyObject_IsInstance(o1, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o1)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o1) == -1)
        return NULL;
    }

    o1 = ((WraptObjectProxyObject *)o1)->wrapped;
  }

  if (PyObject_IsInstance(o2, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o2)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o2) == -1)
        return NULL;
    }

    o2 = ((WraptObjectProxyObject *)o2)->wrapped;
  }

  return PyNumber_Remainder(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_divmod(PyObject *o1, PyObject *o2)
{
  if (PyObject_IsInstance(o1, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o1)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o1) == -1)
        return NULL;
    }

    o1 = ((WraptObjectProxyObject *)o1)->wrapped;
  }

  if (PyObject_IsInstance(o2, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o2)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o2) == -1)
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
  if (PyObject_IsInstance(o1, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o1)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o1) == -1)
        return NULL;
    }

    o1 = ((WraptObjectProxyObject *)o1)->wrapped;
  }

  if (PyObject_IsInstance(o2, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o2)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o2) == -1)
        return NULL;
    }

    o2 = ((WraptObjectProxyObject *)o2)->wrapped;
  }

  return PyNumber_Power(o1, o2, modulo);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_negative(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyNumber_Negative(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_positive(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyNumber_Positive(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_absolute(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyNumber_Absolute(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_bool(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return -1;
  }

  return PyObject_IsTrue(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_invert(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyNumber_Invert(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_lshift(PyObject *o1, PyObject *o2)
{
  if (PyObject_IsInstance(o1, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o1)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o1) == -1)
        return NULL;
    }

    o1 = ((WraptObjectProxyObject *)o1)->wrapped;
  }

  if (PyObject_IsInstance(o2, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o2)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o2) == -1)
        return NULL;
    }

    o2 = ((WraptObjectProxyObject *)o2)->wrapped;
  }

  return PyNumber_Lshift(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_rshift(PyObject *o1, PyObject *o2)
{
  if (PyObject_IsInstance(o1, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o1)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o1) == -1)
        return NULL;
    }

    o1 = ((WraptObjectProxyObject *)o1)->wrapped;
  }

  if (PyObject_IsInstance(o2, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o2)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o2) == -1)
        return NULL;
    }

    o2 = ((WraptObjectProxyObject *)o2)->wrapped;
  }

  return PyNumber_Rshift(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_and(PyObject *o1, PyObject *o2)
{
  if (PyObject_IsInstance(o1, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o1)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o1) == -1)
        return NULL;
    }

    o1 = ((WraptObjectProxyObject *)o1)->wrapped;
  }

  if (PyObject_IsInstance(o2, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o2)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o2) == -1)
        return NULL;
    }

    o2 = ((WraptObjectProxyObject *)o2)->wrapped;
  }

  return PyNumber_And(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_xor(PyObject *o1, PyObject *o2)
{
  if (PyObject_IsInstance(o1, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o1)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o1) == -1)
        return NULL;
    }

    o1 = ((WraptObjectProxyObject *)o1)->wrapped;
  }

  if (PyObject_IsInstance(o2, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o2)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o2) == -1)
        return NULL;
    }

    o2 = ((WraptObjectProxyObject *)o2)->wrapped;
  }

  return PyNumber_Xor(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_or(PyObject *o1, PyObject *o2)
{
  if (PyObject_IsInstance(o1, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o1)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o1) == -1)
        return NULL;
    }

    o1 = ((WraptObjectProxyObject *)o1)->wrapped;
  }

  if (PyObject_IsInstance(o2, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o2)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o2) == -1)
        return NULL;
    }

    o2 = ((WraptObjectProxyObject *)o2)->wrapped;
  }

  return PyNumber_Or(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_long(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyNumber_Long(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_float(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyNumber_Float(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_add(WraptObjectProxyObject *self,
                                              PyObject *other)
{
  PyObject *object = NULL;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  if (PyObject_IsInstance(other, (PyObject *)&WraptObjectProxy_Type))
    other = ((WraptObjectProxyObject *)other)->wrapped;

  if (PyObject_HasAttrString(self->wrapped, "__iadd__"))
  {
    object = PyNumber_InPlaceAdd(self->wrapped, other);

    if (!object)
      return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
  }
  else
  {
    PyObject *result = PyNumber_Add(self->wrapped, other);

    if (!result)
      return NULL;

    PyObject *proxy_type = PyObject_GetAttrString((PyObject *)self, "__object_proxy__");

    if (!proxy_type)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_args = PyTuple_Pack(1, result);

    Py_DECREF(result);

    if (!proxy_args)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_instance = PyObject_Call(proxy_type, proxy_args, NULL);

    Py_DECREF(proxy_type);
    Py_DECREF(proxy_args);

    return proxy_instance;
  }
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_subtract(WraptObjectProxyObject *self,
                                                   PyObject *other)
{
  PyObject *object = NULL;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  if (PyObject_IsInstance(other, (PyObject *)&WraptObjectProxy_Type))
    other = ((WraptObjectProxyObject *)other)->wrapped;

  if (PyObject_HasAttrString(self->wrapped, "__isub__"))
  {
    object = PyNumber_InPlaceSubtract(self->wrapped, other);

    if (!object)
      return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
  }
  else
  {
    PyObject *result = PyNumber_Subtract(self->wrapped, other);

    if (!result)
      return NULL;

    PyObject *proxy_type = PyObject_GetAttrString((PyObject *)self, "__object_proxy__");

    if (!proxy_type)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_args = PyTuple_Pack(1, result);

    Py_DECREF(result);

    if (!proxy_args)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_instance = PyObject_Call(proxy_type, proxy_args, NULL);

    Py_DECREF(proxy_type);
    Py_DECREF(proxy_args);

    return proxy_instance;
  }
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_multiply(WraptObjectProxyObject *self,
                                                   PyObject *other)
{
  PyObject *object = NULL;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  if (PyObject_IsInstance(other, (PyObject *)&WraptObjectProxy_Type))
    other = ((WraptObjectProxyObject *)other)->wrapped;

  if (PyObject_HasAttrString(self->wrapped, "__imul__"))
  {
    object = PyNumber_InPlaceMultiply(self->wrapped, other);

    if (!object)
      return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
  }
  else
  {
    PyObject *result = PyNumber_Multiply(self->wrapped, other);

    if (!result)
      return NULL;

    PyObject *proxy_type = PyObject_GetAttrString((PyObject *)self, "__object_proxy__");

    if (!proxy_type)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_args = PyTuple_Pack(1, result);

    Py_DECREF(result);

    if (!proxy_args)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_instance = PyObject_Call(proxy_type, proxy_args, NULL);

    Py_DECREF(proxy_type);
    Py_DECREF(proxy_args);

    return proxy_instance;
  }
}

/* ------------------------------------------------------------------------- */

static PyObject *
WraptObjectProxy_inplace_remainder(WraptObjectProxyObject *self,
                                   PyObject *other)
{
  PyObject *object = NULL;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  if (PyObject_IsInstance(other, (PyObject *)&WraptObjectProxy_Type))
    other = ((WraptObjectProxyObject *)other)->wrapped;

  if (PyObject_HasAttrString(self->wrapped, "__imod__"))
  {
    object = PyNumber_InPlaceRemainder(self->wrapped, other);

    if (!object)
      return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
  }
  else
  {
    PyObject *result = PyNumber_Remainder(self->wrapped, other);

    if (!result)
      return NULL;

    PyObject *proxy_type = PyObject_GetAttrString((PyObject *)self, "__object_proxy__");

    if (!proxy_type)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_args = PyTuple_Pack(1, result);

    Py_DECREF(result);

    if (!proxy_args)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_instance = PyObject_Call(proxy_type, proxy_args, NULL);

    Py_DECREF(proxy_type);
    Py_DECREF(proxy_args);

    return proxy_instance;
  }
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_power(WraptObjectProxyObject *self,
                                                PyObject *other,
                                                PyObject *modulo)
{
  PyObject *object = NULL;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  if (PyObject_IsInstance(other, (PyObject *)&WraptObjectProxy_Type))
    other = ((WraptObjectProxyObject *)other)->wrapped;

  if (PyObject_HasAttrString(self->wrapped, "__ipow__"))
  {
    object = PyNumber_InPlacePower(self->wrapped, other, modulo);

    if (!object)
      return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
  }
  else
  {
    PyObject *result = PyNumber_Power(self->wrapped, other, modulo);

    if (!result)
      return NULL;

    PyObject *proxy_type = PyObject_GetAttrString((PyObject *)self, "__object_proxy__");

    if (!proxy_type)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_args = PyTuple_Pack(1, result);

    Py_DECREF(result);

    if (!proxy_args)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_instance = PyObject_Call(proxy_type, proxy_args, NULL);

    Py_DECREF(proxy_type);
    Py_DECREF(proxy_args);

    return proxy_instance;
  }
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_lshift(WraptObjectProxyObject *self,
                                                 PyObject *other)
{
  PyObject *object = NULL;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  if (PyObject_IsInstance(other, (PyObject *)&WraptObjectProxy_Type))
    other = ((WraptObjectProxyObject *)other)->wrapped;

  if (PyObject_HasAttrString(self->wrapped, "__ilshift__"))
  {
    object = PyNumber_InPlaceLshift(self->wrapped, other);

    if (!object)
      return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
  }
  else
  {
    PyObject *result = PyNumber_Lshift(self->wrapped, other);

    if (!result)
      return NULL;

    PyObject *proxy_type = PyObject_GetAttrString((PyObject *)self, "__object_proxy__");

    if (!proxy_type)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_args = PyTuple_Pack(1, result);

    Py_DECREF(result);

    if (!proxy_args)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_instance = PyObject_Call(proxy_type, proxy_args, NULL);

    Py_DECREF(proxy_type);
    Py_DECREF(proxy_args);

    return proxy_instance;
  }
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_rshift(WraptObjectProxyObject *self,
                                                 PyObject *other)
{
  PyObject *object = NULL;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  if (PyObject_IsInstance(other, (PyObject *)&WraptObjectProxy_Type))
    other = ((WraptObjectProxyObject *)other)->wrapped;

  if (PyObject_HasAttrString(self->wrapped, "__irshift__"))
  {
    object = PyNumber_InPlaceRshift(self->wrapped, other);

    if (!object)
      return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
  }
  else
  {
    PyObject *result = PyNumber_Rshift(self->wrapped, other);

    if (!result)
      return NULL;

    PyObject *proxy_type = PyObject_GetAttrString((PyObject *)self, "__object_proxy__");

    if (!proxy_type)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_args = PyTuple_Pack(1, result);

    Py_DECREF(result);

    if (!proxy_args)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_instance = PyObject_Call(proxy_type, proxy_args, NULL);

    Py_DECREF(proxy_type);
    Py_DECREF(proxy_args);

    return proxy_instance;
  }
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_and(WraptObjectProxyObject *self,
                                              PyObject *other)
{
  PyObject *object = NULL;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  if (PyObject_IsInstance(other, (PyObject *)&WraptObjectProxy_Type))
    other = ((WraptObjectProxyObject *)other)->wrapped;

  if (PyObject_HasAttrString(self->wrapped, "__iand__"))
  {
    object = PyNumber_InPlaceAnd(self->wrapped, other);

    if (!object)
      return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
  }
  else
  {
    PyObject *result = PyNumber_And(self->wrapped, other);

    if (!result)
      return NULL;

    PyObject *proxy_type = PyObject_GetAttrString((PyObject *)self, "__object_proxy__");

    if (!proxy_type)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_args = PyTuple_Pack(1, result);

    Py_DECREF(result);

    if (!proxy_args)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_instance = PyObject_Call(proxy_type, proxy_args, NULL);

    Py_DECREF(proxy_type);
    Py_DECREF(proxy_args);

    return proxy_instance;
  }
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_xor(WraptObjectProxyObject *self,
                                              PyObject *other)
{
  PyObject *object = NULL;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  if (PyObject_IsInstance(other, (PyObject *)&WraptObjectProxy_Type))
    other = ((WraptObjectProxyObject *)other)->wrapped;

  if (PyObject_HasAttrString(self->wrapped, "__ixor__"))
  {
    object = PyNumber_InPlaceXor(self->wrapped, other);

    if (!object)
      return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
  }
  else
  {
    PyObject *result = PyNumber_Xor(self->wrapped, other);

    if (!result)
      return NULL;

    PyObject *proxy_type = PyObject_GetAttrString((PyObject *)self, "__object_proxy__");

    if (!proxy_type)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_args = PyTuple_Pack(1, result);

    Py_DECREF(result);

    if (!proxy_args)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_instance = PyObject_Call(proxy_type, proxy_args, NULL);

    Py_DECREF(proxy_type);
    Py_DECREF(proxy_args);

    return proxy_instance;
  }
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_or(WraptObjectProxyObject *self,
                                             PyObject *other)
{
  PyObject *object = NULL;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  if (PyObject_IsInstance(other, (PyObject *)&WraptObjectProxy_Type))
    other = ((WraptObjectProxyObject *)other)->wrapped;

  if (PyObject_HasAttrString(self->wrapped, "__ior__"))
  {
    object = PyNumber_InPlaceOr(self->wrapped, other);

    if (!object)
      return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
  }
  else
  {
    PyObject *result = PyNumber_Or(self->wrapped, other);

    if (!result)
      return NULL;

    PyObject *proxy_type = PyObject_GetAttrString((PyObject *)self, "__object_proxy__");

    if (!proxy_type)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_args = PyTuple_Pack(1, result);

    Py_DECREF(result);

    if (!proxy_args)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_instance = PyObject_Call(proxy_type, proxy_args, NULL);

    Py_DECREF(proxy_type);
    Py_DECREF(proxy_args);

    return proxy_instance;
  }
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_floor_divide(PyObject *o1, PyObject *o2)
{
  if (PyObject_IsInstance(o1, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o1)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o1) == -1)
        return NULL;
    }

    o1 = ((WraptObjectProxyObject *)o1)->wrapped;
  }

  if (PyObject_IsInstance(o2, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o2)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o2) == -1)
        return NULL;
    }

    o2 = ((WraptObjectProxyObject *)o2)->wrapped;
  }

  return PyNumber_FloorDivide(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_true_divide(PyObject *o1, PyObject *o2)
{
  if (PyObject_IsInstance(o1, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o1)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o1) == -1)
        return NULL;
    }

    o1 = ((WraptObjectProxyObject *)o1)->wrapped;
  }

  if (PyObject_IsInstance(o2, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o2)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o2) == -1)
        return NULL;
    }

    o2 = ((WraptObjectProxyObject *)o2)->wrapped;
  }

  return PyNumber_TrueDivide(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *
WraptObjectProxy_inplace_floor_divide(WraptObjectProxyObject *self,
                                      PyObject *other)
{
  PyObject *object = NULL;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  if (PyObject_IsInstance(other, (PyObject *)&WraptObjectProxy_Type))
    other = ((WraptObjectProxyObject *)other)->wrapped;

  if (PyObject_HasAttrString(self->wrapped, "__ifloordiv__"))
  {
    object = PyNumber_InPlaceFloorDivide(self->wrapped, other);

    if (!object)
      return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
  }
  else
  {
    PyObject *result = PyNumber_FloorDivide(self->wrapped, other);

    if (!result)
      return NULL;

    PyObject *proxy_type = PyObject_GetAttrString((PyObject *)self, "__object_proxy__");

    if (!proxy_type)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_args = PyTuple_Pack(1, result);

    Py_DECREF(result);

    if (!proxy_args)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_instance = PyObject_Call(proxy_type, proxy_args, NULL);

    Py_DECREF(proxy_type);
    Py_DECREF(proxy_args);

    return proxy_instance;
  }
}

/* ------------------------------------------------------------------------- */

static PyObject *
WraptObjectProxy_inplace_true_divide(WraptObjectProxyObject *self,
                                     PyObject *other)
{
  PyObject *object = NULL;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  if (PyObject_IsInstance(other, (PyObject *)&WraptObjectProxy_Type))
    other = ((WraptObjectProxyObject *)other)->wrapped;

  if (PyObject_HasAttrString(self->wrapped, "__itruediv__"))
  {
    object = PyNumber_InPlaceTrueDivide(self->wrapped, other);

    if (!object)
      return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
  }
  else
  {
    PyObject *result = PyNumber_TrueDivide(self->wrapped, other);

    if (!result)
      return NULL;

    PyObject *proxy_type = PyObject_GetAttrString((PyObject *)self, "__object_proxy__");

    if (!proxy_type)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_args = PyTuple_Pack(1, result);

    Py_DECREF(result);

    if (!proxy_args)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_instance = PyObject_Call(proxy_type, proxy_args, NULL);

    Py_DECREF(proxy_type);
    Py_DECREF(proxy_args);

    return proxy_instance;
  }
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_index(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyNumber_Index(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_matrix_multiply(PyObject *o1, PyObject *o2)
{
  if (PyObject_IsInstance(o1, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o1)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o1) == -1)
        return NULL;
    }

    o1 = ((WraptObjectProxyObject *)o1)->wrapped;
  }

  if (PyObject_IsInstance(o2, (PyObject *)&WraptObjectProxy_Type))
  {
    if (!((WraptObjectProxyObject *)o2)->wrapped)
    {
      if (raise_uninitialized_wrapper_error((WraptObjectProxyObject *)o2) == -1)
        return NULL;
    }

    o2 = ((WraptObjectProxyObject *)o2)->wrapped;
  }

  return PyNumber_MatrixMultiply(o1, o2);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_inplace_matrix_multiply(
    WraptObjectProxyObject *self, PyObject *other)
{
  PyObject *object = NULL;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  if (PyObject_IsInstance(other, (PyObject *)&WraptObjectProxy_Type))
    other = ((WraptObjectProxyObject *)other)->wrapped;

  if (PyObject_HasAttrString(self->wrapped, "__imatmul__"))
  {
    object = PyNumber_InPlaceMatrixMultiply(self->wrapped, other);

    if (!object)
      return NULL;

    Py_DECREF(self->wrapped);
    self->wrapped = object;

    Py_INCREF(self);
    return (PyObject *)self;
  }
  else
  {
    PyObject *result = PyNumber_MatrixMultiply(self->wrapped, other);

    if (!result)
      return NULL;

    PyObject *proxy_type = PyObject_GetAttrString((PyObject *)self, "__object_proxy__");

    if (!proxy_type)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_args = PyTuple_Pack(1, result);

    Py_DECREF(result);

    if (!proxy_args)
    {
      Py_DECREF(proxy_type);
      return NULL;
    }

    PyObject *proxy_instance = PyObject_Call(proxy_type, proxy_args, NULL);

    Py_DECREF(proxy_type);
    Py_DECREF(proxy_args);

    return proxy_instance;
  }
}

/* ------------------------------------------------------------------------- */

static Py_ssize_t WraptObjectProxy_length(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return -1;
  }

  return PyObject_Length(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_contains(WraptObjectProxyObject *self,
                                     PyObject *value)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return -1;
  }

  return PySequence_Contains(self->wrapped, value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_getitem(WraptObjectProxyObject *self,
                                          PyObject *key)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyObject_GetItem(self->wrapped, key);
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_setitem(WraptObjectProxyObject *self, PyObject *key,
                                    PyObject *value)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return -1;
  }

  if (value == NULL)
    return PyObject_DelItem(self->wrapped, key);
  else
    return PyObject_SetItem(self->wrapped, key, value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_self_setattr(WraptObjectProxyObject *self,
                                               PyObject *args)
{
  PyObject *name = NULL;
  PyObject *value = NULL;

  if (!PyArg_ParseTuple(args, "UO:__self_setattr__", &name, &value))
    return NULL;

  if (PyObject_GenericSetAttr((PyObject *)self, name, value) != 0)
  {
    return NULL;
  }

  Py_INCREF(Py_None);
  return Py_None;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_dir(WraptObjectProxyObject *self,
                                      PyObject *args)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyObject_Dir(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_enter(WraptObjectProxyObject *self,
                                        PyObject *args, PyObject *kwds)
{
  PyObject *method = NULL;
  PyObject *result = NULL;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
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

static PyObject *WraptObjectProxy_exit(WraptObjectProxyObject *self,
                                       PyObject *args, PyObject *kwds)
{
  PyObject *method = NULL;
  PyObject *result = NULL;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
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

static PyObject *WraptObjectProxy_aenter(WraptObjectProxyObject *self,
                                         PyObject *args, PyObject *kwds)
{
  PyObject *method = NULL;
  PyObject *result = NULL;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  method = PyObject_GetAttrString(self->wrapped, "__aenter__");

  if (!method)
    return NULL;

  result = PyObject_Call(method, args, kwds);

  Py_DECREF(method);

  return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_aexit(WraptObjectProxyObject *self,
                                        PyObject *args, PyObject *kwds)
{
  PyObject *method = NULL;
  PyObject *result = NULL;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  method = PyObject_GetAttrString(self->wrapped, "__aexit__");

  if (!method)
    return NULL;

  result = PyObject_Call(method, args, kwds);

  Py_DECREF(method);

  return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_copy(WraptObjectProxyObject *self,
                                       PyObject *args, PyObject *kwds)
{
  PyErr_SetString(PyExc_NotImplementedError,
                  "object proxy must define __copy__()");

  return NULL;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_deepcopy(WraptObjectProxyObject *self,
                                           PyObject *args, PyObject *kwds)
{
  PyErr_SetString(PyExc_NotImplementedError,
                  "object proxy must define __deepcopy__()");

  return NULL;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_reduce(WraptObjectProxyObject *self,
                                         PyObject *args, PyObject *kwds)
{
  PyErr_SetString(PyExc_NotImplementedError,
                  "object proxy must define __reduce__()");

  return NULL;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_reduce_ex(WraptObjectProxyObject *self,
                                            PyObject *args, PyObject *kwds)
{
  PyErr_SetString(PyExc_NotImplementedError,
                  "object proxy must define __reduce_ex__()");

  return NULL;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_bytes(WraptObjectProxyObject *self,
                                        PyObject *args)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyObject_Bytes(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_format(WraptObjectProxyObject *self,
                                         PyObject *args)
{
  PyObject *format_spec = NULL;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  if (!PyArg_ParseTuple(args, "|O:format", &format_spec))
    return NULL;

  return PyObject_Format(self->wrapped, format_spec);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_reversed(WraptObjectProxyObject *self,
                                           PyObject *args)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyObject_CallFunctionObjArgs((PyObject *)&PyReversed_Type,
                                      self->wrapped, NULL);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_round(WraptObjectProxyObject *self,
                                        PyObject *args, PyObject *kwds)
{
  PyObject *ndigits = NULL;

  PyObject *module = NULL;
  PyObject *round = NULL;

  PyObject *result = NULL;

  char *const kwlist[] = {"ndigits", NULL};

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O:ObjectProxy", kwlist,
                                   &ndigits))
  {
    return NULL;
  }

  module = PyImport_ImportModule("builtins");

  if (!module)
    return NULL;

  round = PyObject_GetAttrString(module, "round");

  if (!round)
  {
    Py_DECREF(module);
    return NULL;
  }

  Py_INCREF(round);
  Py_DECREF(module);

  result = PyObject_CallFunctionObjArgs(round, self->wrapped, ndigits, NULL);

  Py_DECREF(round);

  return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_complex(WraptObjectProxyObject *self,
                                          PyObject *args)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyObject_CallFunctionObjArgs((PyObject *)&PyComplex_Type,
                                      self->wrapped, NULL);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_mro_entries(WraptObjectProxyObject *self,
                                              PyObject *args, PyObject *kwds)
{
  PyObject *wrapped = NULL;
  PyObject *mro_entries_method = NULL;
  PyObject *result = NULL;
  int is_type = 0;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  wrapped = self->wrapped;

  // Check if wrapped is a type (class).

  is_type = PyType_Check(wrapped);

  // If wrapped is not a type and has __mro_entries__, forward to it.

  if (!is_type)
  {
    mro_entries_method = PyObject_GetAttrString(wrapped, "__mro_entries__");

    if (mro_entries_method)
    {
      // Call wrapped.__mro_entries__(bases).

      result = PyObject_Call(mro_entries_method, args, kwds);

      Py_DECREF(mro_entries_method);

      return result;
    }
    else
    {
      PyErr_Clear();
    }
  }

  return Py_BuildValue("(O)", wrapped);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_name(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyObject_GetAttrString(self->wrapped, "__name__");
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_set_name(WraptObjectProxyObject *self,
                                     PyObject *value)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return -1;
  }

  return PyObject_SetAttrString(self->wrapped, "__name__", value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_qualname(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyObject_GetAttrString(self->wrapped, "__qualname__");
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_set_qualname(WraptObjectProxyObject *self,
                                         PyObject *value)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return -1;
  }

  return PyObject_SetAttrString(self->wrapped, "__qualname__", value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_module(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyObject_GetAttrString(self->wrapped, "__module__");
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_set_module(WraptObjectProxyObject *self,
                                       PyObject *value)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return -1;
  }

  if (PyObject_SetAttrString(self->wrapped, "__module__", value) == -1)
    return -1;

  return PyDict_SetItemString(self->dict, "__module__", value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_doc(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyObject_GetAttrString(self->wrapped, "__doc__");
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_set_doc(WraptObjectProxyObject *self,
                                    PyObject *value)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return -1;
  }

  if (PyObject_SetAttrString(self->wrapped, "__doc__", value) == -1)
    return -1;

  return PyDict_SetItemString(self->dict, "__doc__", value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_class(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyObject_GetAttrString(self->wrapped, "__class__");
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_set_class(WraptObjectProxyObject *self,
                                      PyObject *value)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return -1;
  }

  return PyObject_SetAttrString(self->wrapped, "__class__", value);
}

/* ------------------------------------------------------------------------- */

static PyObject *
WraptObjectProxy_get_annotations(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyObject_GetAttrString(self->wrapped, "__annotations__");
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_set_annotations(WraptObjectProxyObject *self,
                                            PyObject *value)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return -1;
  }

  return PyObject_SetAttrString(self->wrapped, "__annotations__", value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_wrapped(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  Py_INCREF(self->wrapped);
  return self->wrapped;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_get_object_proxy(WraptObjectProxyObject *self)
{
  Py_INCREF(&WraptObjectProxy_Type);
  return (PyObject *)&WraptObjectProxy_Type;
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_set_wrapped(WraptObjectProxyObject *self,
                                        PyObject *value)
{
  static PyObject *fixups_str = NULL;

  PyObject *fixups = NULL;

  if (!value)
  {
    PyErr_SetString(PyExc_TypeError, "__wrapped__ must be an object");
    return -1;
  }

  Py_INCREF(value);
  Py_XDECREF(self->wrapped);

  self->wrapped = value;

  if (!fixups_str)
  {
    fixups_str = PyUnicode_InternFromString("__wrapped_setattr_fixups__");
  }

  fixups = PyObject_GetAttr((PyObject *)self, fixups_str);

  if (fixups)
  {
    PyObject *result = NULL;

    result = PyObject_CallObject(fixups, NULL);
    Py_DECREF(fixups);

    if (!result)
      return -1;

    Py_DECREF(result);
  }
  else
    PyErr_Clear();

  return 0;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_getattro(WraptObjectProxyObject *self,
                                           PyObject *name)
{
  PyObject *object = NULL;
  PyObject *result = NULL;

  static PyObject *getattr_str = NULL;

  object = PyObject_GenericGetAttr((PyObject *)self, name);

  if (object)
    return object;

  if (!PyErr_ExceptionMatches(PyExc_AttributeError))
    return NULL;

  PyErr_Clear();

  if (!getattr_str)
  {
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

static PyObject *WraptObjectProxy_getattr(WraptObjectProxyObject *self,
                                          PyObject *args)
{
  PyObject *name = NULL;

  if (!PyArg_ParseTuple(args, "U:__getattr__", &name))
    return NULL;

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyObject_GetAttr(self->wrapped, name);
}

/* ------------------------------------------------------------------------- */

static int WraptObjectProxy_setattro(WraptObjectProxyObject *self,
                                     PyObject *name, PyObject *value)
{
  static PyObject *self_str = NULL;
  static PyObject *startswith_str = NULL;

  PyObject *match = NULL;

  if (!startswith_str)
  {
    startswith_str = PyUnicode_InternFromString("startswith");
  }

  if (!self_str)
  {
    self_str = PyUnicode_InternFromString("_self_");
  }

  match = PyObject_CallMethodObjArgs(name, startswith_str, self_str, NULL);

  if (match == Py_True)
  {
    Py_DECREF(match);

    return PyObject_GenericSetAttr((PyObject *)self, name, value);
  }
  else if (!match)
    PyErr_Clear();

  Py_XDECREF(match);

  if (PyObject_HasAttr((PyObject *)Py_TYPE(self), name))
    return PyObject_GenericSetAttr((PyObject *)self, name, value);

  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return -1;
  }

  return PyObject_SetAttr(self->wrapped, name, value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_richcompare(WraptObjectProxyObject *self,
                                              PyObject *other, int opcode)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyObject_RichCompare(self->wrapped, other, opcode);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptObjectProxy_iter(WraptObjectProxyObject *self)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyObject_GetIter(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyNumberMethods WraptObjectProxy_as_number = {
    (binaryfunc)WraptObjectProxy_add,               /*nb_add*/
    (binaryfunc)WraptObjectProxy_subtract,          /*nb_subtract*/
    (binaryfunc)WraptObjectProxy_multiply,          /*nb_multiply*/
    (binaryfunc)WraptObjectProxy_remainder,         /*nb_remainder*/
    (binaryfunc)WraptObjectProxy_divmod,            /*nb_divmod*/
    (ternaryfunc)WraptObjectProxy_power,            /*nb_power*/
    (unaryfunc)WraptObjectProxy_negative,           /*nb_negative*/
    (unaryfunc)WraptObjectProxy_positive,           /*nb_positive*/
    (unaryfunc)WraptObjectProxy_absolute,           /*nb_absolute*/
    (inquiry)WraptObjectProxy_bool,                 /*nb_nonzero/nb_bool*/
    (unaryfunc)WraptObjectProxy_invert,             /*nb_invert*/
    (binaryfunc)WraptObjectProxy_lshift,            /*nb_lshift*/
    (binaryfunc)WraptObjectProxy_rshift,            /*nb_rshift*/
    (binaryfunc)WraptObjectProxy_and,               /*nb_and*/
    (binaryfunc)WraptObjectProxy_xor,               /*nb_xor*/
    (binaryfunc)WraptObjectProxy_or,                /*nb_or*/
    (unaryfunc)WraptObjectProxy_long,               /*nb_int*/
    0,                                              /*nb_long/nb_reserved*/
    (unaryfunc)WraptObjectProxy_float,              /*nb_float*/
    (binaryfunc)WraptObjectProxy_inplace_add,       /*nb_inplace_add*/
    (binaryfunc)WraptObjectProxy_inplace_subtract,  /*nb_inplace_subtract*/
    (binaryfunc)WraptObjectProxy_inplace_multiply,  /*nb_inplace_multiply*/
    (binaryfunc)WraptObjectProxy_inplace_remainder, /*nb_inplace_remainder*/
    (ternaryfunc)WraptObjectProxy_inplace_power,    /*nb_inplace_power*/
    (binaryfunc)WraptObjectProxy_inplace_lshift,    /*nb_inplace_lshift*/
    (binaryfunc)WraptObjectProxy_inplace_rshift,    /*nb_inplace_rshift*/
    (binaryfunc)WraptObjectProxy_inplace_and,       /*nb_inplace_and*/
    (binaryfunc)WraptObjectProxy_inplace_xor,       /*nb_inplace_xor*/
    (binaryfunc)WraptObjectProxy_inplace_or,        /*nb_inplace_or*/
    (binaryfunc)WraptObjectProxy_floor_divide,      /*nb_floor_divide*/
    (binaryfunc)WraptObjectProxy_true_divide,       /*nb_true_divide*/
    (binaryfunc)
        WraptObjectProxy_inplace_floor_divide,            /*nb_inplace_floor_divide*/
    (binaryfunc)WraptObjectProxy_inplace_true_divide,     /*nb_inplace_true_divide*/
    (unaryfunc)WraptObjectProxy_index,                    /*nb_index*/
    (binaryfunc)WraptObjectProxy_matrix_multiply,         /*nb_matrix_multiply*/
    (binaryfunc)WraptObjectProxy_inplace_matrix_multiply, /*nb_inplace_matrix_multiply*/
};

static PySequenceMethods WraptObjectProxy_as_sequence = {
    (lenfunc)WraptObjectProxy_length,      /*sq_length*/
    0,                                     /*sq_concat*/
    0,                                     /*sq_repeat*/
    0,                                     /*sq_item*/
    0,                                     /*sq_slice*/
    0,                                     /*sq_ass_item*/
    0,                                     /*sq_ass_slice*/
    (objobjproc)WraptObjectProxy_contains, /* sq_contains */
};

static PyMappingMethods WraptObjectProxy_as_mapping = {
    (lenfunc)WraptObjectProxy_length,        /*mp_length*/
    (binaryfunc)WraptObjectProxy_getitem,    /*mp_subscript*/
    (objobjargproc)WraptObjectProxy_setitem, /*mp_ass_subscript*/
};

static PyMethodDef WraptObjectProxy_methods[] = {
    {"__self_setattr__", (PyCFunction)WraptObjectProxy_self_setattr,
     METH_VARARGS, 0},
    {"__dir__", (PyCFunction)WraptObjectProxy_dir, METH_NOARGS, 0},
    {"__enter__", (PyCFunction)WraptObjectProxy_enter,
     METH_VARARGS | METH_KEYWORDS, 0},
    {"__exit__", (PyCFunction)WraptObjectProxy_exit,
     METH_VARARGS | METH_KEYWORDS, 0},
    {"__aenter__", (PyCFunction)WraptObjectProxy_aenter,
     METH_VARARGS | METH_KEYWORDS, 0},
    {"__aexit__", (PyCFunction)WraptObjectProxy_aexit,
     METH_VARARGS | METH_KEYWORDS, 0},
    {"__copy__", (PyCFunction)WraptObjectProxy_copy, METH_NOARGS, 0},
    {"__deepcopy__", (PyCFunction)WraptObjectProxy_deepcopy,
     METH_VARARGS | METH_KEYWORDS, 0},
    {"__reduce__", (PyCFunction)WraptObjectProxy_reduce, METH_NOARGS, 0},
    {"__reduce_ex__", (PyCFunction)WraptObjectProxy_reduce_ex,
     METH_VARARGS | METH_KEYWORDS, 0},
    {"__getattr__", (PyCFunction)WraptObjectProxy_getattr, METH_VARARGS, 0},
    {"__bytes__", (PyCFunction)WraptObjectProxy_bytes, METH_NOARGS, 0},
    {"__format__", (PyCFunction)WraptObjectProxy_format, METH_VARARGS, 0},
    {"__reversed__", (PyCFunction)WraptObjectProxy_reversed, METH_NOARGS, 0},
    {"__round__", (PyCFunction)WraptObjectProxy_round,
     METH_VARARGS | METH_KEYWORDS, 0},
    {"__complex__", (PyCFunction)WraptObjectProxy_complex, METH_NOARGS, 0},
    {"__mro_entries__", (PyCFunction)WraptObjectProxy_mro_entries,
     METH_VARARGS | METH_KEYWORDS, 0},
    {NULL, NULL},
};

static PyGetSetDef WraptObjectProxy_getset[] = {
    {"__name__", (getter)WraptObjectProxy_get_name,
     (setter)WraptObjectProxy_set_name, 0},
    {"__qualname__", (getter)WraptObjectProxy_get_qualname,
     (setter)WraptObjectProxy_set_qualname, 0},
    {"__module__", (getter)WraptObjectProxy_get_module,
     (setter)WraptObjectProxy_set_module, 0},
    {"__doc__", (getter)WraptObjectProxy_get_doc,
     (setter)WraptObjectProxy_set_doc, 0},
    {"__class__", (getter)WraptObjectProxy_get_class,
     (setter)WraptObjectProxy_set_class, 0},
    {"__annotations__", (getter)WraptObjectProxy_get_annotations,
     (setter)WraptObjectProxy_set_annotations, 0},
    {"__wrapped__", (getter)WraptObjectProxy_get_wrapped,
     (setter)WraptObjectProxy_set_wrapped, 0},
    {"__object_proxy__", (getter)WraptObjectProxy_get_object_proxy, 0, 0},
    {NULL},
};

PyTypeObject WraptObjectProxy_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "ObjectProxy", /*tp_name*/
    sizeof(WraptObjectProxyObject),               /*tp_basicsize*/
    0,                                            /*tp_itemsize*/
    /* methods */
    (destructor)WraptObjectProxy_dealloc,                          /*tp_dealloc*/
    0,                                                             /*tp_print*/
    0,                                                             /*tp_getattr*/
    0,                                                             /*tp_setattr*/
    0,                                                             /*tp_as_async*/
    (unaryfunc)WraptObjectProxy_repr,                              /*tp_repr*/
    &WraptObjectProxy_as_number,                                   /*tp_as_number*/
    &WraptObjectProxy_as_sequence,                                 /*tp_as_sequence*/
    &WraptObjectProxy_as_mapping,                                  /*tp_as_mapping*/
    (hashfunc)WraptObjectProxy_hash,                               /*tp_hash*/
    0,                                                             /*tp_call*/
    (unaryfunc)WraptObjectProxy_str,                               /*tp_str*/
    (getattrofunc)WraptObjectProxy_getattro,                       /*tp_getattro*/
    (setattrofunc)WraptObjectProxy_setattro,                       /*tp_setattro*/
    0,                                                             /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC, /*tp_flags*/
    0,                                                             /*tp_doc*/
    (traverseproc)WraptObjectProxy_traverse,                       /*tp_traverse*/
    (inquiry)WraptObjectProxy_clear,                               /*tp_clear*/
    (richcmpfunc)WraptObjectProxy_richcompare,                     /*tp_richcompare*/
    offsetof(WraptObjectProxyObject, weakreflist),                 /*tp_weaklistoffset*/
    0, /* (getiterfunc)WraptObjectProxy_iter, */                   /*tp_iter*/
    0,                                                             /*tp_iternext*/
    WraptObjectProxy_methods,                                      /*tp_methods*/
    0,                                                             /*tp_members*/
    WraptObjectProxy_getset,                                       /*tp_getset*/
    0,                                                             /*tp_base*/
    0,                                                             /*tp_dict*/
    0,                                                             /*tp_descr_get*/
    0,                                                             /*tp_descr_set*/
    offsetof(WraptObjectProxyObject, dict),                        /*tp_dictoffset*/
    (initproc)WraptObjectProxy_init,                               /*tp_init*/
    PyType_GenericAlloc,                                           /*tp_alloc*/
    WraptObjectProxy_new,                                          /*tp_new*/
    PyObject_GC_Del,                                               /*tp_free*/
    0,                                                             /*tp_is_gc*/
};

/* ------------------------------------------------------------------------- */

static PyObject *WraptCallableObjectProxy_call(WraptObjectProxyObject *self,
                                               PyObject *args, PyObject *kwds)
{
  if (!self->wrapped)
  {
    if (raise_uninitialized_wrapper_error(self) == -1)
      return NULL;
  }

  return PyObject_Call(self->wrapped, args, kwds);
}

/* ------------------------------------------------------------------------- */;

static PyGetSetDef WraptCallableObjectProxy_getset[] = {
    {"__module__", (getter)WraptObjectProxy_get_module,
     (setter)WraptObjectProxy_set_module, 0},
    {"__doc__", (getter)WraptObjectProxy_get_doc,
     (setter)WraptObjectProxy_set_doc, 0},
    {NULL},
};

PyTypeObject WraptCallableObjectProxy_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "CallableObjectProxy", /*tp_name*/
    sizeof(WraptObjectProxyObject),                       /*tp_basicsize*/
    0,                                                    /*tp_itemsize*/
    /* methods */
    0,                                             /*tp_dealloc*/
    0,                                             /*tp_print*/
    0,                                             /*tp_getattr*/
    0,                                             /*tp_setattr*/
    0,                                             /*tp_compare*/
    0,                                             /*tp_repr*/
    0,                                             /*tp_as_number*/
    0,                                             /*tp_as_sequence*/
    0,                                             /*tp_as_mapping*/
    0,                                             /*tp_hash*/
    (ternaryfunc)WraptCallableObjectProxy_call,    /*tp_call*/
    0,                                             /*tp_str*/
    0,                                             /*tp_getattro*/
    0,                                             /*tp_setattro*/
    0,                                             /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,      /*tp_flags*/
    0,                                             /*tp_doc*/
    0,                                             /*tp_traverse*/
    0,                                             /*tp_clear*/
    0,                                             /*tp_richcompare*/
    offsetof(WraptObjectProxyObject, weakreflist), /*tp_weaklistoffset*/
    0,                                             /*tp_iter*/
    0,                                             /*tp_iternext*/
    0,                                             /*tp_methods*/
    0,                                             /*tp_members*/
    WraptCallableObjectProxy_getset,               /*tp_getset*/
    0,                                             /*tp_base*/
    0,                                             /*tp_dict*/
    0,                                             /*tp_descr_get*/
    0,                                             /*tp_descr_set*/
    0,                                             /*tp_dictoffset*/
    (initproc)WraptObjectProxy_init,               /*tp_init*/
    0,                                             /*tp_alloc*/
    0,                                             /*tp_new*/
    0,                                             /*tp_free*/
    0,                                             /*tp_is_gc*/
};

/* ------------------------------------------------------------------------- */

static PyObject *WraptPartialCallableObjectProxy_new(PyTypeObject *type,
                                                     PyObject *args,
                                                     PyObject *kwds)
{
  WraptPartialCallableObjectProxyObject *self;

  self = (WraptPartialCallableObjectProxyObject *)WraptObjectProxy_new(
      type, args, kwds);

  if (!self)
    return NULL;

  self->args = NULL;
  self->kwargs = NULL;

  return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static int WraptPartialCallableObjectProxy_raw_init(
    WraptPartialCallableObjectProxyObject *self, PyObject *wrapped,
    PyObject *args, PyObject *kwargs)
{
  int result = 0;

  result = WraptObjectProxy_raw_init((WraptObjectProxyObject *)self, wrapped);

  if (result == 0)
  {
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

  if (!PyObject_Length(args))
  {
    PyErr_SetString(PyExc_TypeError, "__init__ of partial needs an argument");
    return -1;
  }

  if (PyObject_Length(args) < 1)
  {
    PyErr_SetString(PyExc_TypeError,
                    "partial type takes at least one argument");
    return -1;
  }

  wrapped = PyTuple_GetItem(args, 0);

  if (!PyCallable_Check(wrapped))
  {
    PyErr_SetString(PyExc_TypeError, "the first argument must be callable");
    return -1;
  }

  fnargs = PyTuple_GetSlice(args, 1, PyTuple_Size(args));

  if (!fnargs)
    return -1;

  result =
      WraptPartialCallableObjectProxy_raw_init(self, wrapped, fnargs, kwds);

  Py_DECREF(fnargs);

  return result;
}

/* ------------------------------------------------------------------------- */

static int WraptPartialCallableObjectProxy_traverse(
    WraptPartialCallableObjectProxyObject *self, visitproc visit, void *arg)
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

  if (!self->object_proxy.wrapped)
  {
    if (raise_uninitialized_wrapper_error(&self->object_proxy) == -1)
      return NULL;
  }

  fnargs = PyTuple_New(PyTuple_Size(self->args) + PyTuple_Size(args));

  for (i = 0; i < PyTuple_Size(self->args); i++)
  {
    PyObject *item;
    item = PyTuple_GetItem(self->args, i);
    Py_INCREF(item);
    PyTuple_SetItem(fnargs, i, item);
  }

  offset = PyTuple_Size(self->args);

  for (i = 0; i < PyTuple_Size(args); i++)
  {
    PyObject *item;
    item = PyTuple_GetItem(args, i);
    Py_INCREF(item);
    PyTuple_SetItem(fnargs, offset + i, item);
  }

  fnkwargs = PyDict_New();

  if (self->kwargs && PyDict_Update(fnkwargs, self->kwargs) == -1)
  {
    Py_DECREF(fnargs);
    Py_DECREF(fnkwargs);
    return NULL;
  }

  if (kwds && PyDict_Update(fnkwargs, kwds) == -1)
  {
    Py_DECREF(fnargs);
    Py_DECREF(fnkwargs);
    return NULL;
  }

  result = PyObject_Call(self->object_proxy.wrapped, fnargs, fnkwargs);

  Py_DECREF(fnargs);
  Py_DECREF(fnkwargs);

  return result;
}

/* ------------------------------------------------------------------------- */;

static PyGetSetDef WraptPartialCallableObjectProxy_getset[] = {
    {"__module__", (getter)WraptObjectProxy_get_module,
     (setter)WraptObjectProxy_set_module, 0},
    {"__doc__", (getter)WraptObjectProxy_get_doc,
     (setter)WraptObjectProxy_set_doc, 0},
    {NULL},
};

PyTypeObject WraptPartialCallableObjectProxy_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "PartialCallableObjectProxy", /*tp_name*/
    sizeof(WraptPartialCallableObjectProxyObject),               /*tp_basicsize*/
    0,                                                           /*tp_itemsize*/
    /* methods */
    (destructor)WraptPartialCallableObjectProxy_dealloc,           /*tp_dealloc*/
    0,                                                             /*tp_print*/
    0,                                                             /*tp_getattr*/
    0,                                                             /*tp_setattr*/
    0,                                                             /*tp_compare*/
    0,                                                             /*tp_repr*/
    0,                                                             /*tp_as_number*/
    0,                                                             /*tp_as_sequence*/
    0,                                                             /*tp_as_mapping*/
    0,                                                             /*tp_hash*/
    (ternaryfunc)WraptPartialCallableObjectProxy_call,             /*tp_call*/
    0,                                                             /*tp_str*/
    0,                                                             /*tp_getattro*/
    0,                                                             /*tp_setattro*/
    0,                                                             /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC, /*tp_flags*/
    0,                                                             /*tp_doc*/
    (traverseproc)WraptPartialCallableObjectProxy_traverse,        /*tp_traverse*/
    (inquiry)WraptPartialCallableObjectProxy_clear,                /*tp_clear*/
    0,                                                             /*tp_richcompare*/
    offsetof(WraptObjectProxyObject, weakreflist),                 /*tp_weaklistoffset*/
    0,                                                             /*tp_iter*/
    0,                                                             /*tp_iternext*/
    0,                                                             /*tp_methods*/
    0,                                                             /*tp_members*/
    WraptPartialCallableObjectProxy_getset,                        /*tp_getset*/
    0,                                                             /*tp_base*/
    0,                                                             /*tp_dict*/
    0,                                                             /*tp_descr_get*/
    0,                                                             /*tp_descr_set*/
    0,                                                             /*tp_dictoffset*/
    (initproc)WraptPartialCallableObjectProxy_init,                /*tp_init*/
    0,                                                             /*tp_alloc*/
    WraptPartialCallableObjectProxy_new,                           /*tp_new*/
    0,                                                             /*tp_free*/
    0,                                                             /*tp_is_gc*/
};

/* ------------------------------------------------------------------------- */

static PyObject *WraptFunctionWrapperBase_new(PyTypeObject *type,
                                              PyObject *args, PyObject *kwds)
{
  WraptFunctionWrapperObject *self;

  self = (WraptFunctionWrapperObject *)WraptObjectProxy_new(type, args, kwds);

  if (!self)
    return NULL;

  self->instance = NULL;
  self->wrapper = NULL;
  self->enabled = NULL;
  self->binding = NULL;
  self->parent = NULL;
  self->owner = NULL;

  return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static int WraptFunctionWrapperBase_raw_init(
    WraptFunctionWrapperObject *self, PyObject *wrapped, PyObject *instance,
    PyObject *wrapper, PyObject *enabled, PyObject *binding, PyObject *parent,
    PyObject *owner)
{
  int result = 0;

  result = WraptObjectProxy_raw_init((WraptObjectProxyObject *)self, wrapped);

  if (result == 0)
  {
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

    Py_INCREF(owner);
    Py_XDECREF(self->owner);
    self->owner = owner;
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
  PyObject *owner = Py_None;

  static PyObject *callable_str = NULL;

  char *const kwlist[] = {"wrapped", "instance", "wrapper", "enabled",
                          "binding", "parent", "owner", NULL};

  if (!callable_str)
  {
    callable_str = PyUnicode_InternFromString("callable");
  }

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOO|OOOO:FunctionWrapperBase",
                                   kwlist, &wrapped, &instance, &wrapper,
                                   &enabled, &binding, &parent, &owner))
  {
    return -1;
  }

  if (!binding)
    binding = callable_str;

  return WraptFunctionWrapperBase_raw_init(self, wrapped, instance, wrapper,
                                           enabled, binding, parent, owner);
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
  Py_VISIT(self->owner);

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
  Py_CLEAR(self->owner);

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

static PyObject *WraptFunctionWrapperBase_call(WraptFunctionWrapperObject *self,
                                               PyObject *args, PyObject *kwds)
{
  PyObject *param_kwds = NULL;

  PyObject *result = NULL;

  static PyObject *function_str = NULL;
  static PyObject *callable_str = NULL;
  static PyObject *classmethod_str = NULL;
  static PyObject *instancemethod_str = NULL;

  if (!function_str)
  {
    function_str = PyUnicode_InternFromString("function");
    callable_str = PyUnicode_InternFromString("callable");
    classmethod_str = PyUnicode_InternFromString("classmethod");
    instancemethod_str = PyUnicode_InternFromString("instancemethod");
  }

  if (self->enabled != Py_None)
  {
    if (PyCallable_Check(self->enabled))
    {
      PyObject *object = NULL;

      object = PyObject_CallFunctionObjArgs(self->enabled, NULL);

      if (!object)
        return NULL;

      if (PyObject_Not(object))
      {
        Py_DECREF(object);
        return PyObject_Call(self->object_proxy.wrapped, args, kwds);
      }

      Py_DECREF(object);
    }
    else if (PyObject_Not(self->enabled))
    {
      return PyObject_Call(self->object_proxy.wrapped, args, kwds);
    }
  }

  if (!kwds)
  {
    param_kwds = PyDict_New();
    kwds = param_kwds;
  }

  if ((self->instance == Py_None) &&
      (self->binding == function_str ||
       PyObject_RichCompareBool(self->binding, function_str, Py_EQ) == 1 ||
       self->binding == instancemethod_str ||
       PyObject_RichCompareBool(self->binding, instancemethod_str, Py_EQ) ==
           1 ||
       self->binding == callable_str ||
       PyObject_RichCompareBool(self->binding, callable_str, Py_EQ) == 1 ||
       self->binding == classmethod_str ||
       PyObject_RichCompareBool(self->binding, classmethod_str, Py_EQ) == 1))
  {

    PyObject *instance = NULL;

    instance = PyObject_GetAttrString(self->object_proxy.wrapped, "__self__");

    if (instance)
    {
      result = PyObject_CallFunctionObjArgs(self->wrapper,
                                            self->object_proxy.wrapped,
                                            instance, args, kwds, NULL);

      Py_XDECREF(param_kwds);

      Py_DECREF(instance);

      return result;
    }
    else
      PyErr_Clear();
  }

  result =
      PyObject_CallFunctionObjArgs(self->wrapper, self->object_proxy.wrapped,
                                   self->instance, args, kwds, NULL);

  Py_XDECREF(param_kwds);

  return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *
WraptFunctionWrapperBase_descr_get(WraptFunctionWrapperObject *self,
                                   PyObject *obj, PyObject *type)
{
  PyObject *bound_type = NULL;
  PyObject *descriptor = NULL;
  PyObject *result = NULL;

  static PyObject *bound_type_str = NULL;
  static PyObject *function_str = NULL;
  static PyObject *callable_str = NULL;
  static PyObject *builtin_str = NULL;
  static PyObject *class_str = NULL;
  static PyObject *instancemethod_str = NULL;

  if (!bound_type_str)
  {
    bound_type_str = PyUnicode_InternFromString("__bound_function_wrapper__");
  }

  if (!function_str)
  {
    function_str = PyUnicode_InternFromString("function");
    callable_str = PyUnicode_InternFromString("callable");
    builtin_str = PyUnicode_InternFromString("builtin");
    class_str = PyUnicode_InternFromString("class");
    instancemethod_str = PyUnicode_InternFromString("instancemethod");
  }

  if (self->parent == Py_None)
  {
    if (self->binding == builtin_str ||
        PyObject_RichCompareBool(self->binding, builtin_str, Py_EQ) == 1)
    {
      Py_INCREF(self);
      return (PyObject *)self;
    }

    if (self->binding == class_str ||
        PyObject_RichCompareBool(self->binding, class_str, Py_EQ) == 1)
    {
      Py_INCREF(self);
      return (PyObject *)self;
    }

    if (Py_TYPE(self->object_proxy.wrapped)->tp_descr_get == NULL)
    {
      Py_INCREF(self);
      return (PyObject *)self;
    }

    descriptor = (Py_TYPE(self->object_proxy.wrapped)->tp_descr_get)(
        self->object_proxy.wrapped, obj, type);

    if (!descriptor)
      return NULL;

    if (Py_TYPE(self) != &WraptFunctionWrapper_Type)
    {
      bound_type = PyObject_GenericGetAttr((PyObject *)self, bound_type_str);

      if (!bound_type)
        PyErr_Clear();
    }

    if (obj == NULL)
      obj = Py_None;

    result = PyObject_CallFunctionObjArgs(
        bound_type ? bound_type : (PyObject *)&WraptBoundFunctionWrapper_Type,
        descriptor, obj, self->wrapper, self->enabled, self->binding, self,
        type, NULL);

    Py_XDECREF(bound_type);
    Py_DECREF(descriptor);

    return result;
  }

  if (self->instance == Py_None &&
      (self->binding == function_str ||
       PyObject_RichCompareBool(self->binding, function_str, Py_EQ) == 1 ||
       self->binding == instancemethod_str ||
       PyObject_RichCompareBool(self->binding, instancemethod_str, Py_EQ) ==
           1 ||
       self->binding == callable_str ||
       PyObject_RichCompareBool(self->binding, callable_str, Py_EQ) == 1))
  {

    PyObject *wrapped = NULL;

    static PyObject *wrapped_str = NULL;

    if (!wrapped_str)
    {
      wrapped_str = PyUnicode_InternFromString("__wrapped__");
    }

    wrapped = PyObject_GetAttr(self->parent, wrapped_str);

    if (!wrapped)
      return NULL;

    if (Py_TYPE(wrapped)->tp_descr_get == NULL)
    {
      PyErr_Format(PyExc_AttributeError,
                   "'%s' object has no attribute '__get__'",
                   Py_TYPE(wrapped)->tp_name);
      Py_DECREF(wrapped);
      return NULL;
    }

    descriptor = (Py_TYPE(wrapped)->tp_descr_get)(wrapped, obj, type);

    Py_DECREF(wrapped);

    if (!descriptor)
      return NULL;

    if (Py_TYPE(self->parent) != &WraptFunctionWrapper_Type)
    {
      bound_type =
          PyObject_GenericGetAttr((PyObject *)self->parent, bound_type_str);

      if (!bound_type)
        PyErr_Clear();
    }

    if (obj == NULL)
      obj = Py_None;

    result = PyObject_CallFunctionObjArgs(
        bound_type ? bound_type : (PyObject *)&WraptBoundFunctionWrapper_Type,
        descriptor, obj, self->wrapper, self->enabled, self->binding,
        self->parent, type, NULL);

    Py_XDECREF(bound_type);
    Py_DECREF(descriptor);

    return result;
  }

  Py_INCREF(self);
  return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static PyObject *
WraptFunctionWrapperBase_set_name(WraptFunctionWrapperObject *self,
                                  PyObject *args, PyObject *kwds)
{
  PyObject *method = NULL;
  PyObject *result = NULL;

  if (!self->object_proxy.wrapped)
  {
    if (raise_uninitialized_wrapper_error(&self->object_proxy) == -1)
      return NULL;
  }

  method = PyObject_GetAttrString(self->object_proxy.wrapped, "__set_name__");

  if (!method)
  {
    PyErr_Clear();
    Py_INCREF(Py_None);
    return Py_None;
  }

  result = PyObject_Call(method, args, kwds);

  Py_DECREF(method);

  return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *
WraptFunctionWrapperBase_instancecheck(WraptFunctionWrapperObject *self,
                                       PyObject *instance)
{
  PyObject *result = NULL;

  int check = 0;

  if (!self->object_proxy.wrapped)
  {
    if (raise_uninitialized_wrapper_error(&self->object_proxy) == -1)
      return NULL;
  }

  check = PyObject_IsInstance(instance, self->object_proxy.wrapped);

  if (check < 0)
  {
    return NULL;
  }

  result = check ? Py_True : Py_False;

  Py_INCREF(result);
  return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *
WraptFunctionWrapperBase_subclasscheck(WraptFunctionWrapperObject *self,
                                       PyObject *args)
{
  PyObject *subclass = NULL;
  PyObject *object = NULL;
  PyObject *result = NULL;

  int check = 0;

  if (!self->object_proxy.wrapped)
  {
    if (raise_uninitialized_wrapper_error(&self->object_proxy) == -1)
      return NULL;
  }

  if (!PyArg_ParseTuple(args, "O", &subclass))
    return NULL;

  object = PyObject_GetAttrString(subclass, "__wrapped__");

  if (!object)
    PyErr_Clear();

  check = PyObject_IsSubclass(object ? object : subclass,
                              self->object_proxy.wrapped);

  Py_XDECREF(object);

  if (check == -1)
    return NULL;

  result = check ? Py_True : Py_False;

  Py_INCREF(result);

  return result;
}

/* ------------------------------------------------------------------------- */

static PyObject *
WraptFunctionWrapperBase_get_self_instance(WraptFunctionWrapperObject *self,
                                           void *closure)
{
  if (!self->instance)
  {
    Py_INCREF(Py_None);
    return Py_None;
  }

  Py_INCREF(self->instance);
  return self->instance;
}

/* ------------------------------------------------------------------------- */

static PyObject *
WraptFunctionWrapperBase_get_self_wrapper(WraptFunctionWrapperObject *self,
                                          void *closure)
{
  if (!self->wrapper)
  {
    Py_INCREF(Py_None);
    return Py_None;
  }

  Py_INCREF(self->wrapper);
  return self->wrapper;
}

/* ------------------------------------------------------------------------- */

static PyObject *
WraptFunctionWrapperBase_get_self_enabled(WraptFunctionWrapperObject *self,
                                          void *closure)
{
  if (!self->enabled)
  {
    Py_INCREF(Py_None);
    return Py_None;
  }

  Py_INCREF(self->enabled);
  return self->enabled;
}

/* ------------------------------------------------------------------------- */

static PyObject *
WraptFunctionWrapperBase_get_self_binding(WraptFunctionWrapperObject *self,
                                          void *closure)
{
  if (!self->binding)
  {
    Py_INCREF(Py_None);
    return Py_None;
  }

  Py_INCREF(self->binding);
  return self->binding;
}

/* ------------------------------------------------------------------------- */

static PyObject *
WraptFunctionWrapperBase_get_self_parent(WraptFunctionWrapperObject *self,
                                         void *closure)
{
  if (!self->parent)
  {
    Py_INCREF(Py_None);
    return Py_None;
  }

  Py_INCREF(self->parent);
  return self->parent;
}

/* ------------------------------------------------------------------------- */

static PyObject *
WraptFunctionWrapperBase_get_self_owner(WraptFunctionWrapperObject *self,
                                        void *closure)
{
  if (!self->owner)
  {
    Py_INCREF(Py_None);
    return Py_None;
  }

  Py_INCREF(self->owner);
  return self->owner;
}

/* ------------------------------------------------------------------------- */;

static PyMethodDef WraptFunctionWrapperBase_methods[] = {
    {"__set_name__", (PyCFunction)WraptFunctionWrapperBase_set_name,
     METH_VARARGS | METH_KEYWORDS, 0},
    {"__instancecheck__", (PyCFunction)WraptFunctionWrapperBase_instancecheck,
     METH_O, 0},
    {"__subclasscheck__", (PyCFunction)WraptFunctionWrapperBase_subclasscheck,
     METH_VARARGS, 0},
    {NULL, NULL},
};

/* ------------------------------------------------------------------------- */;

static PyGetSetDef WraptFunctionWrapperBase_getset[] = {
    {"__module__", (getter)WraptObjectProxy_get_module,
     (setter)WraptObjectProxy_set_module, 0},
    {"__doc__", (getter)WraptObjectProxy_get_doc,
     (setter)WraptObjectProxy_set_doc, 0},
    {"_self_instance", (getter)WraptFunctionWrapperBase_get_self_instance, NULL,
     0},
    {"_self_wrapper", (getter)WraptFunctionWrapperBase_get_self_wrapper, NULL,
     0},
    {"_self_enabled", (getter)WraptFunctionWrapperBase_get_self_enabled, NULL,
     0},
    {"_self_binding", (getter)WraptFunctionWrapperBase_get_self_binding, NULL,
     0},
    {"_self_parent", (getter)WraptFunctionWrapperBase_get_self_parent, NULL, 0},
    {"_self_owner", (getter)WraptFunctionWrapperBase_get_self_owner, NULL, 0},
    {NULL},
};

PyTypeObject WraptFunctionWrapperBase_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "_FunctionWrapperBase", /*tp_name*/
    sizeof(WraptFunctionWrapperObject),                    /*tp_basicsize*/
    0,                                                     /*tp_itemsize*/
    /* methods */
    (destructor)WraptFunctionWrapperBase_dealloc,                  /*tp_dealloc*/
    0,                                                             /*tp_print*/
    0,                                                             /*tp_getattr*/
    0,                                                             /*tp_setattr*/
    0,                                                             /*tp_compare*/
    0,                                                             /*tp_repr*/
    0,                                                             /*tp_as_number*/
    0,                                                             /*tp_as_sequence*/
    0,                                                             /*tp_as_mapping*/
    0,                                                             /*tp_hash*/
    (ternaryfunc)WraptFunctionWrapperBase_call,                    /*tp_call*/
    0,                                                             /*tp_str*/
    0,                                                             /*tp_getattro*/
    0,                                                             /*tp_setattro*/
    0,                                                             /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC, /*tp_flags*/
    0,                                                             /*tp_doc*/
    (traverseproc)WraptFunctionWrapperBase_traverse,               /*tp_traverse*/
    (inquiry)WraptFunctionWrapperBase_clear,                       /*tp_clear*/
    0,                                                             /*tp_richcompare*/
    offsetof(WraptObjectProxyObject, weakreflist),                 /*tp_weaklistoffset*/
    0,                                                             /*tp_iter*/
    0,                                                             /*tp_iternext*/
    WraptFunctionWrapperBase_methods,                              /*tp_methods*/
    0,                                                             /*tp_members*/
    WraptFunctionWrapperBase_getset,                               /*tp_getset*/
    0,                                                             /*tp_base*/
    0,                                                             /*tp_dict*/
    (descrgetfunc)WraptFunctionWrapperBase_descr_get,              /*tp_descr_get*/
    0,                                                             /*tp_descr_set*/
    0,                                                             /*tp_dictoffset*/
    (initproc)WraptFunctionWrapperBase_init,                       /*tp_init*/
    0,                                                             /*tp_alloc*/
    WraptFunctionWrapperBase_new,                                  /*tp_new*/
    0,                                                             /*tp_free*/
    0,                                                             /*tp_is_gc*/
};

/* ------------------------------------------------------------------------- */

static PyObject *
WraptBoundFunctionWrapper_call(WraptFunctionWrapperObject *self, PyObject *args,
                               PyObject *kwds)
{
  PyObject *param_args = NULL;
  PyObject *param_kwds = NULL;

  PyObject *wrapped = NULL;
  PyObject *instance = NULL;

  PyObject *result = NULL;

  static PyObject *function_str = NULL;
  static PyObject *callable_str = NULL;

  if (self->enabled != Py_None)
  {
    if (PyCallable_Check(self->enabled))
    {
      PyObject *object = NULL;

      object = PyObject_CallFunctionObjArgs(self->enabled, NULL);

      if (!object)
        return NULL;

      if (PyObject_Not(object))
      {
        Py_DECREF(object);
        return PyObject_Call(self->object_proxy.wrapped, args, kwds);
      }

      Py_DECREF(object);
    }
    else if (PyObject_Not(self->enabled))
    {
      return PyObject_Call(self->object_proxy.wrapped, args, kwds);
    }
  }

  if (!function_str)
  {
    function_str = PyUnicode_InternFromString("function");
    callable_str = PyUnicode_InternFromString("callable");
  }

  /*
   * We need to do things different depending on whether we are likely
   * wrapping an instance method vs a static method or class method.
   */

  if (self->binding == function_str ||
      PyObject_RichCompareBool(self->binding, function_str, Py_EQ) == 1 ||
      self->binding == callable_str ||
      PyObject_RichCompareBool(self->binding, callable_str, Py_EQ) == 1)
  {

    // if (self->instance == Py_None) {
    //     /*
    //      * This situation can occur where someone is calling the
    //      * instancemethod via the class type and passing the
    //      * instance as the first argument. We need to shift the args
    //      * before making the call to the wrapper and effectively
    //      * bind the instance to the wrapped function using a partial
    //      * so the wrapper doesn't see anything as being different.
    //      */

    //     if (PyTuple_Size(args) == 0) {
    //         PyErr_SetString(PyExc_TypeError,
    //                 "missing 1 required positional argument");
    //         return NULL;
    //     }

    //     instance = PyTuple_GetItem(args, 0);

    //     if (!instance)
    //         return NULL;

    //     wrapped = PyObject_CallFunctionObjArgs(
    //             (PyObject *)&WraptPartialCallableObjectProxy_Type,
    //             self->object_proxy.wrapped, instance, NULL);

    //     if (!wrapped)
    //         return NULL;

    //     param_args = PyTuple_GetSlice(args, 1, PyTuple_Size(args));

    //     if (!param_args) {
    //         Py_DECREF(wrapped);
    //         return NULL;
    //     }

    //     args = param_args;
    // }

    if (self->instance == Py_None && PyTuple_Size(args) != 0)
    {
      /*
       * This situation can occur where someone is calling the
       * instancemethod via the class type and passing the
       * instance as the first argument. We need to shift the args
       * before making the call to the wrapper and effectively
       * bind the instance to the wrapped function using a partial
       * so the wrapper doesn't see anything as being different.
       */

      instance = PyTuple_GetItem(args, 0);

      if (!instance)
        return NULL;

      if (PyObject_IsInstance(instance, self->owner) == 1)
      {
        wrapped = PyObject_CallFunctionObjArgs(
            (PyObject *)&WraptPartialCallableObjectProxy_Type,
            self->object_proxy.wrapped, instance, NULL);

        if (!wrapped)
          return NULL;

        param_args = PyTuple_GetSlice(args, 1, PyTuple_Size(args));

        if (!param_args)
        {
          Py_DECREF(wrapped);
          return NULL;
        }

        args = param_args;
      }
      else
      {
        instance = self->instance;
      }
    }
    else
    {
      instance = self->instance;
    }

    if (!wrapped)
    {
      Py_INCREF(self->object_proxy.wrapped);
      wrapped = self->object_proxy.wrapped;
    }

    if (!kwds)
    {
      param_kwds = PyDict_New();
      kwds = param_kwds;
    }

    result = PyObject_CallFunctionObjArgs(self->wrapper, wrapped, instance,
                                          args, kwds, NULL);

    Py_XDECREF(param_args);
    Py_XDECREF(param_kwds);
    Py_DECREF(wrapped);

    return result;
  }
  else
  {
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

    instance = PyObject_GetAttrString(self->object_proxy.wrapped, "__self__");

    if (!instance)
    {
      PyErr_Clear();
      Py_INCREF(Py_None);
      instance = Py_None;
    }

    if (!kwds)
    {
      param_kwds = PyDict_New();
      kwds = param_kwds;
    }

    result = PyObject_CallFunctionObjArgs(
        self->wrapper, self->object_proxy.wrapped, instance, args, kwds, NULL);

    Py_XDECREF(param_kwds);

    Py_DECREF(instance);

    return result;
  }
}

/* ------------------------------------------------------------------------- */

static PyGetSetDef WraptBoundFunctionWrapper_getset[] = {
    {"__module__", (getter)WraptObjectProxy_get_module,
     (setter)WraptObjectProxy_set_module, 0},
    {"__doc__", (getter)WraptObjectProxy_get_doc,
     (setter)WraptObjectProxy_set_doc, 0},
    {NULL},
};

PyTypeObject WraptBoundFunctionWrapper_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "BoundFunctionWrapper", /*tp_name*/
    sizeof(WraptFunctionWrapperObject),                    /*tp_basicsize*/
    0,                                                     /*tp_itemsize*/
    /* methods */
    0,                                             /*tp_dealloc*/
    0,                                             /*tp_print*/
    0,                                             /*tp_getattr*/
    0,                                             /*tp_setattr*/
    0,                                             /*tp_compare*/
    0,                                             /*tp_repr*/
    0,                                             /*tp_as_number*/
    0,                                             /*tp_as_sequence*/
    0,                                             /*tp_as_mapping*/
    0,                                             /*tp_hash*/
    (ternaryfunc)WraptBoundFunctionWrapper_call,   /*tp_call*/
    0,                                             /*tp_str*/
    0,                                             /*tp_getattro*/
    0,                                             /*tp_setattro*/
    0,                                             /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,      /*tp_flags*/
    0,                                             /*tp_doc*/
    0,                                             /*tp_traverse*/
    0,                                             /*tp_clear*/
    0,                                             /*tp_richcompare*/
    offsetof(WraptObjectProxyObject, weakreflist), /*tp_weaklistoffset*/
    0,                                             /*tp_iter*/
    0,                                             /*tp_iternext*/
    0,                                             /*tp_methods*/
    0,                                             /*tp_members*/
    WraptBoundFunctionWrapper_getset,              /*tp_getset*/
    0,                                             /*tp_base*/
    0,                                             /*tp_dict*/
    0,                                             /*tp_descr_get*/
    0,                                             /*tp_descr_set*/
    0,                                             /*tp_dictoffset*/
    0,                                             /*tp_init*/
    0,                                             /*tp_alloc*/
    0,                                             /*tp_new*/
    0,                                             /*tp_free*/
    0,                                             /*tp_is_gc*/
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

  static PyObject *function_str = NULL;
  static PyObject *classmethod_str = NULL;
  static PyObject *staticmethod_str = NULL;
  static PyObject *callable_str = NULL;
  static PyObject *builtin_str = NULL;
  static PyObject *class_str = NULL;
  static PyObject *instancemethod_str = NULL;

  int result = 0;

  char *const kwlist[] = {"wrapped", "wrapper", "enabled", NULL};

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|O:FunctionWrapper", kwlist,
                                   &wrapped, &wrapper, &enabled))
  {
    return -1;
  }

  if (!function_str)
  {
    function_str = PyUnicode_InternFromString("function");
  }

  if (!classmethod_str)
  {
    classmethod_str = PyUnicode_InternFromString("classmethod");
  }

  if (!staticmethod_str)
  {
    staticmethod_str = PyUnicode_InternFromString("staticmethod");
  }

  if (!callable_str)
  {
    callable_str = PyUnicode_InternFromString("callable");
  }

  if (!builtin_str)
  {
    builtin_str = PyUnicode_InternFromString("builtin");
  }

  if (!class_str)
  {
    class_str = PyUnicode_InternFromString("class");
  }

  if (!instancemethod_str)
  {
    instancemethod_str = PyUnicode_InternFromString("instancemethod");
  }

  if (PyObject_IsInstance(wrapped,
                          (PyObject *)&WraptFunctionWrapperBase_Type))
  {
    binding = PyObject_GetAttrString(wrapped, "_self_binding");
  }

  if (!binding)
  {
    if (PyCFunction_Check(wrapped))
    {
      binding = builtin_str;
    }
    else if (PyObject_IsInstance(wrapped, (PyObject *)&PyFunction_Type))
    {
      binding = function_str;
    }
    else if (PyObject_IsInstance(wrapped, (PyObject *)&PyClassMethod_Type))
    {
      binding = classmethod_str;
    }
    else if (PyObject_IsInstance(wrapped, (PyObject *)&PyType_Type))
    {
      binding = class_str;
    }
    else if (PyObject_IsInstance(wrapped, (PyObject *)&PyStaticMethod_Type))
    {
      binding = staticmethod_str;
    }
    else if ((instance = PyObject_GetAttrString(wrapped, "__self__")) != 0)
    {
      if (PyObject_IsInstance(instance, (PyObject *)&PyType_Type))
      {
        binding = classmethod_str;
      }
      else if (PyObject_IsInstance(wrapped, (PyObject *)&PyMethod_Type))
      {
        binding = instancemethod_str;
      }
      else
        binding = callable_str;

      Py_DECREF(instance);
    }
    else
    {
      PyErr_Clear();

      binding = callable_str;
    }
  }

  result = WraptFunctionWrapperBase_raw_init(
      self, wrapped, Py_None, wrapper, enabled, binding, Py_None, Py_None);

  return result;
}

/* ------------------------------------------------------------------------- */

static PyGetSetDef WraptFunctionWrapper_getset[] = {
    {"__module__", (getter)WraptObjectProxy_get_module,
     (setter)WraptObjectProxy_set_module, 0},
    {"__doc__", (getter)WraptObjectProxy_get_doc,
     (setter)WraptObjectProxy_set_doc, 0},
    {NULL},
};

PyTypeObject WraptFunctionWrapper_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "FunctionWrapper", /*tp_name*/
    sizeof(WraptFunctionWrapperObject),               /*tp_basicsize*/
    0,                                                /*tp_itemsize*/
    /* methods */
    0,                                             /*tp_dealloc*/
    0,                                             /*tp_print*/
    0,                                             /*tp_getattr*/
    0,                                             /*tp_setattr*/
    0,                                             /*tp_compare*/
    0,                                             /*tp_repr*/
    0,                                             /*tp_as_number*/
    0,                                             /*tp_as_sequence*/
    0,                                             /*tp_as_mapping*/
    0,                                             /*tp_hash*/
    0,                                             /*tp_call*/
    0,                                             /*tp_str*/
    0,                                             /*tp_getattro*/
    0,                                             /*tp_setattro*/
    0,                                             /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,      /*tp_flags*/
    0,                                             /*tp_doc*/
    0,                                             /*tp_traverse*/
    0,                                             /*tp_clear*/
    0,                                             /*tp_richcompare*/
    offsetof(WraptObjectProxyObject, weakreflist), /*tp_weaklistoffset*/
    0,                                             /*tp_iter*/
    0,                                             /*tp_iternext*/
    0,                                             /*tp_methods*/
    0,                                             /*tp_members*/
    WraptFunctionWrapper_getset,                   /*tp_getset*/
    0,                                             /*tp_base*/
    0,                                             /*tp_dict*/
    0,                                             /*tp_descr_get*/
    0,                                             /*tp_descr_set*/
    0,                                             /*tp_dictoffset*/
    (initproc)WraptFunctionWrapper_init,           /*tp_init*/
    0,                                             /*tp_alloc*/
    0,                                             /*tp_new*/
    0,                                             /*tp_free*/
    0,                                             /*tp_is_gc*/
};

/* ------------------------------------------------------------------------- */

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "_wrappers", /* m_name */
    NULL,        /* m_doc */
    -1,          /* m_size */
    NULL,        /* m_methods */
    NULL,        /* m_reload */
    NULL,        /* m_traverse */
    NULL,        /* m_clear */
    NULL,        /* m_free */
};

static PyObject *moduleinit(void)
{
  PyObject *module;

  module = PyModule_Create(&moduledef);

  if (module == NULL)
    return NULL;

  if (PyType_Ready(&WraptObjectProxy_Type) < 0)
    return NULL;

  /* Ensure that inheritance relationships specified. */

  WraptCallableObjectProxy_Type.tp_base = &WraptObjectProxy_Type;
  WraptPartialCallableObjectProxy_Type.tp_base = &WraptObjectProxy_Type;
  WraptFunctionWrapperBase_Type.tp_base = &WraptObjectProxy_Type;
  WraptBoundFunctionWrapper_Type.tp_base = &WraptFunctionWrapperBase_Type;
  WraptFunctionWrapper_Type.tp_base = &WraptFunctionWrapperBase_Type;

  if (PyType_Ready(&WraptCallableObjectProxy_Type) < 0)
    return NULL;
  if (PyType_Ready(&WraptPartialCallableObjectProxy_Type) < 0)
    return NULL;
  if (PyType_Ready(&WraptFunctionWrapperBase_Type) < 0)
    return NULL;
  if (PyType_Ready(&WraptBoundFunctionWrapper_Type) < 0)
    return NULL;
  if (PyType_Ready(&WraptFunctionWrapper_Type) < 0)
    return NULL;

  Py_INCREF(&WraptObjectProxy_Type);
  PyModule_AddObject(module, "ObjectProxy", (PyObject *)&WraptObjectProxy_Type);
  Py_INCREF(&WraptCallableObjectProxy_Type);
  PyModule_AddObject(module, "CallableObjectProxy",
                     (PyObject *)&WraptCallableObjectProxy_Type);
  Py_INCREF(&WraptPartialCallableObjectProxy_Type);
  PyModule_AddObject(module, "PartialCallableObjectProxy",
                     (PyObject *)&WraptPartialCallableObjectProxy_Type);
  Py_INCREF(&WraptFunctionWrapper_Type);
  PyModule_AddObject(module, "FunctionWrapper",
                     (PyObject *)&WraptFunctionWrapper_Type);

  Py_INCREF(&WraptFunctionWrapperBase_Type);
  PyModule_AddObject(module, "_FunctionWrapperBase",
                     (PyObject *)&WraptFunctionWrapperBase_Type);
  Py_INCREF(&WraptBoundFunctionWrapper_Type);
  PyModule_AddObject(module, "BoundFunctionWrapper",
                     (PyObject *)&WraptBoundFunctionWrapper_Type);

#ifdef Py_GIL_DISABLED
  PyUnstable_Module_SetGIL(module, Py_MOD_GIL_NOT_USED);
#endif

  return module;
}

PyMODINIT_FUNC PyInit__wrappers(void) { return moduleinit(); }

/* ------------------------------------------------------------------------- */
