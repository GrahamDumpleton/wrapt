/* ------------------------------------------------------------------------- */

#include "Python.h"

#include "structmember.h"

#ifndef PyVarObject_HEAD_INIT
#define PyVarObject_HEAD_INIT(type, size) PyObject_HEAD_INIT(type) size,
#endif

/* ------------------------------------------------------------------------- */

typedef struct {
    PyObject_HEAD
    PyObject *wrapped;
    PyObject *wrapper;
    PyObject *target;
} WraptWrapperBaseObject;

PyTypeObject WraptWrapperBase_Type;

/* ------------------------------------------------------------------------- */

static PyObject *WraptWrapperBase_new(PyTypeObject *type,
        PyObject *args, PyObject *kwds)
{
    WraptWrapperBaseObject *self;

    self = (WraptWrapperBaseObject *)type->tp_alloc(type, 0);

    if (!self)
        return NULL;

    self->wrapped = NULL;
    self->wrapper = NULL;
    self->target = NULL;

    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static int WraptWrapperBase_init(WraptWrapperBaseObject *self,
        PyObject *args, PyObject *kwds)
{
    PyObject *wrapped = NULL;
    PyObject *wrapper = NULL;
    PyObject *target = Py_None;

    PyObject *name = NULL;
    PyObject *object = NULL;

    static char *kwlist[] = { "wrapped", "wrapper", "target", NULL };

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|O:WrapperBase",
            kwlist, &wrapped, &wrapper, &target)) {
        return -1;
    }

    Py_INCREF(wrapped);
    Py_INCREF(wrapper);

    self->wrapped = wrapped;
    self->wrapper = wrapper;

    if (target == Py_None) {
        object = PyObject_GetAttrString(wrapped, "__wrapped__");

        if (object) {
            Py_INCREF(object);
            self->target = object;
        }
        else {
            PyErr_Clear();

            Py_INCREF(wrapped);
            self->target = wrapped;
        }

        object = PyObject_GetAttrString(wrapped, "__name__");

        if (object) {
#if PY_MAJOR_VERSION >= 3
            name = PyUnicode_FromString("__name__");
#else
            name = PyString_FromString("__name__");
#endif
            PyObject_GenericSetAttr((PyObject *)self, name, object);
            Py_DECREF(name);
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
        }
        else
            PyErr_Clear();
    }
    else {
        Py_INCREF(target);
        self->target = target;

        object = PyObject_GetAttrString(target, "__name__");

        if (object) {
#if PY_MAJOR_VERSION >= 3
            name = PyUnicode_FromString("__name__");
#else
            name = PyString_FromString("__name__");
#endif
            PyObject_GenericSetAttr((PyObject *)self, name, object);
            Py_DECREF(name);
        }
        else
            PyErr_Clear();

        object = PyObject_GetAttrString(target, "__qualname__");

        if (object) {
#if PY_MAJOR_VERSION >= 3
            name = PyUnicode_FromString("__qualname__");
#else
            name = PyString_FromString("__qualname__");
#endif
            PyObject_GenericSetAttr((PyObject *)self, name, object);
            Py_DECREF(name);
        }
        else
            PyErr_Clear();
    }

    object = PyObject_GetAttrString(wrapped, "__module__");

    if (object) {
#if PY_MAJOR_VERSION >= 3
        name = PyUnicode_FromString("__module__");
#else
        name = PyString_FromString("__module__");
#endif
        PyObject_GenericSetAttr((PyObject *)self, name, object);
        Py_DECREF(name);
    }
    else
        PyErr_Clear();

    object = PyObject_GetAttrString(wrapped, "__doc__");

    if (object) {
#if PY_MAJOR_VERSION >= 3
        name = PyUnicode_FromString("__doc__");
#else
        name = PyString_FromString("__doc__");
#endif
        PyObject_GenericSetAttr((PyObject *)self, name, object);
        Py_DECREF(name);
    }
    else
        PyErr_Clear();

    return 0;
}

/* ------------------------------------------------------------------------- */

static void WraptWrapperBase_dealloc(WraptWrapperBaseObject *self)
{
    Py_XDECREF(self->wrapped);
    Py_XDECREF(self->wrapper);
    Py_XDECREF(self->target);

    Py_TYPE(self)->tp_free(self);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptWrapperBase_get_wrapped(
        WraptWrapperBaseObject *self, void *closure)
{
    if (!self->wrapped) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    Py_INCREF(self->wrapped);
    return self->wrapped;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptWrapperBase_get_wrapper(
        WraptWrapperBaseObject *self, void *closure)
{
    if (!self->wrapper) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    Py_INCREF(self->wrapper);
    return self->wrapper;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptWrapperBase_get_target(
        WraptWrapperBaseObject *self, void *closure)
{
    if (!self->target) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    Py_INCREF(self->target);
    return self->target;
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptWrapperBase_get_class(
        WraptWrapperBaseObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyObject_GetAttrString(self->wrapped, "__class__");
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptWrapperBase_getattro(
        WraptWrapperBaseObject *self, PyObject *name)
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

static int WraptWrapperBase_setattro(
        WraptWrapperBaseObject *self, PyObject *name, PyObject *value)
{
    static PyObject *self_prefix = NULL;

    PyObject *match = NULL;

    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return -1;
    }

    if (!self_prefix)
        self_prefix = PyUnicode_FromString("_self_");

    match = PyEval_CallMethod(name, "startswith", "(O)", self_prefix);

    if (match == Py_True)
        return PyObject_GenericSetAttr((PyObject *)self, name, value);

    Py_XDECREF(match);

    return PyObject_SetAttr(self->wrapped, name, value);
}

/* ------------------------------------------------------------------------- */

static PyObject *WraptWrapperBase_iter(WraptWrapperBaseObject *self)
{
    if (!self->wrapped) {
      PyErr_SetString(PyExc_ValueError, "wrapper has not been initialised");
      return NULL;
    }

    return PyObject_GetIter(self->wrapped);
}

/* ------------------------------------------------------------------------- */

static PyGetSetDef WraptWrapperBase_getset[] = {
    { "_self_wrapped",      (getter)WraptWrapperBase_get_wrapped,
                            NULL, 0 },
    { "_self_wrapper",      (getter)WraptWrapperBase_get_wrapper,
                            NULL, 0 },
    { "_self_target",       (getter)WraptWrapperBase_get_target,
                            NULL, 0 },
    { "__class__",          (getter)WraptWrapperBase_get_class,
                            NULL, 0 },
    { NULL },
};

PyTypeObject WraptWrapperBase_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "_wrappers.WrapperBase", /*tp_name*/
    sizeof(WraptWrapperBaseObject), /*tp_basicsize*/
    0,                      /*tp_itemsize*/
    /* methods */
    (destructor)WraptWrapperBase_dealloc, /*tp_dealloc*/
    0,                      /*tp_print*/
    0,                      /*tp_getattr*/
    0,                      /*tp_setattr*/
    0,                      /*tp_compare*/
    0,                      /*tp_repr*/
    0,                      /*tp_as_number*/
    0,                      /*tp_as_sequence*/
    0,                      /*tp_as_mapping*/
    0,                      /*tp_hash*/
    0,                      /*tp_call*/
    0,                      /*tp_str*/
    (getattrofunc)WraptWrapperBase_getattro, /*tp_getattro*/
    (setattrofunc)WraptWrapperBase_setattro, /*tp_setattro*/
    0,                      /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT |
    Py_TPFLAGS_BASETYPE,    /*tp_flags*/
    0,                      /*tp_doc*/
    0,                      /*tp_traverse*/
    0,                      /*tp_clear*/
    0,                      /*tp_richcompare*/
    0,                      /*tp_weaklistoffset*/
    (getiterfunc)WraptWrapperBase_iter, /*tp_iter*/
    0,                      /*tp_iternext*/
    0,                      /*tp_methods*/
    0,                      /*tp_members*/
    WraptWrapperBase_getset, /*tp_getset*/
    0,                      /*tp_base*/
    0,                      /*tp_dict*/
    0,                      /*tp_descr_get*/
    0,                      /*tp_descr_set*/
    0,                      /*tp_dictoffset*/
    (initproc)WraptWrapperBase_init, /*tp_init*/
    0,                      /*tp_alloc*/
    WraptWrapperBase_new,  /*tp_new*/
    0,                      /*tp_free*/
    0,                      /*tp_is_gc*/
}

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

    if (PyType_Ready(&WraptWrapperBase_Type) < 0)
        return NULL;

    Py_INCREF(&WraptWrapperBase_Type);
    PyModule_AddObject(module, "WrapperBase",
            (PyObject *)&WraptWrapperBase_Type);

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
