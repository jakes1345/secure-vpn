/****************************************************************************
** Meta object code from reading C++ file 'downloadmanager.h'
**
** Created by: The Qt Meta Object Compiler version 68 (Qt 6.4.2)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include <memory>
#include "../../../src/downloadmanager.h"
#include <QtNetwork/QSslError>
#include <QtCore/qmetatype.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'downloadmanager.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 68
#error "This file was generated using the moc from 6.4.2. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

#ifndef Q_CONSTINIT
#define Q_CONSTINIT
#endif

QT_BEGIN_MOC_NAMESPACE
QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace {
struct qt_meta_stringdata_DownloadItem_t {
    uint offsetsAndSizes[22];
    char stringdata0[13];
    char stringdata1[16];
    char stringdata2[1];
    char stringdata3[9];
    char stringdata4[7];
    char stringdata5[6];
    char stringdata6[19];
    char stringdata7[14];
    char stringdata8[11];
    char stringdata9[11];
    char stringdata10[9];
};
#define QT_MOC_LITERAL(ofs, len) \
    uint(sizeof(qt_meta_stringdata_DownloadItem_t::offsetsAndSizes) + ofs), len 
Q_CONSTINIT static const qt_meta_stringdata_DownloadItem_t qt_meta_stringdata_DownloadItem = {
    {
        QT_MOC_LITERAL(0, 12),  // "DownloadItem"
        QT_MOC_LITERAL(13, 15),  // "progressChanged"
        QT_MOC_LITERAL(29, 0),  // ""
        QT_MOC_LITERAL(30, 8),  // "finished"
        QT_MOC_LITERAL(39, 6),  // "failed"
        QT_MOC_LITERAL(46, 5),  // "error"
        QT_MOC_LITERAL(52, 18),  // "onDownloadProgress"
        QT_MOC_LITERAL(71, 13),  // "bytesReceived"
        QT_MOC_LITERAL(85, 10),  // "bytesTotal"
        QT_MOC_LITERAL(96, 10),  // "onFinished"
        QT_MOC_LITERAL(107, 8)   // "onFailed"
    },
    "DownloadItem",
    "progressChanged",
    "",
    "finished",
    "failed",
    "error",
    "onDownloadProgress",
    "bytesReceived",
    "bytesTotal",
    "onFinished",
    "onFailed"
};
#undef QT_MOC_LITERAL
} // unnamed namespace

Q_CONSTINIT static const uint qt_meta_data_DownloadItem[] = {

 // content:
      10,       // revision
       0,       // classname
       0,    0, // classinfo
       6,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       3,       // signalCount

 // signals: name, argc, parameters, tag, flags, initial metatype offsets
       1,    0,   50,    2, 0x06,    1 /* Public */,
       3,    0,   51,    2, 0x06,    2 /* Public */,
       4,    1,   52,    2, 0x06,    3 /* Public */,

 // slots: name, argc, parameters, tag, flags, initial metatype offsets
       6,    2,   55,    2, 0x08,    5 /* Private */,
       9,    0,   60,    2, 0x08,    8 /* Private */,
      10,    0,   61,    2, 0x08,    9 /* Private */,

 // signals: parameters
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, QMetaType::QString,    5,

 // slots: parameters
    QMetaType::Void, QMetaType::LongLong, QMetaType::LongLong,    7,    8,
    QMetaType::Void,
    QMetaType::Void,

       0        // eod
};

Q_CONSTINIT const QMetaObject DownloadItem::staticMetaObject = { {
    QMetaObject::SuperData::link<QObject::staticMetaObject>(),
    qt_meta_stringdata_DownloadItem.offsetsAndSizes,
    qt_meta_data_DownloadItem,
    qt_static_metacall,
    nullptr,
    qt_incomplete_metaTypeArray<qt_meta_stringdata_DownloadItem_t,
        // Q_OBJECT / Q_GADGET
        QtPrivate::TypeAndForceComplete<DownloadItem, std::true_type>,
        // method 'progressChanged'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'finished'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'failed'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        QtPrivate::TypeAndForceComplete<const QString &, std::false_type>,
        // method 'onDownloadProgress'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        QtPrivate::TypeAndForceComplete<qint64, std::false_type>,
        QtPrivate::TypeAndForceComplete<qint64, std::false_type>,
        // method 'onFinished'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'onFailed'
        QtPrivate::TypeAndForceComplete<void, std::false_type>
    >,
    nullptr
} };

void DownloadItem::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        auto *_t = static_cast<DownloadItem *>(_o);
        (void)_t;
        switch (_id) {
        case 0: _t->progressChanged(); break;
        case 1: _t->finished(); break;
        case 2: _t->failed((*reinterpret_cast< std::add_pointer_t<QString>>(_a[1]))); break;
        case 3: _t->onDownloadProgress((*reinterpret_cast< std::add_pointer_t<qint64>>(_a[1])),(*reinterpret_cast< std::add_pointer_t<qint64>>(_a[2]))); break;
        case 4: _t->onFinished(); break;
        case 5: _t->onFailed(); break;
        default: ;
        }
    } else if (_c == QMetaObject::IndexOfMethod) {
        int *result = reinterpret_cast<int *>(_a[0]);
        {
            using _t = void (DownloadItem::*)();
            if (_t _q_method = &DownloadItem::progressChanged; *reinterpret_cast<_t *>(_a[1]) == _q_method) {
                *result = 0;
                return;
            }
        }
        {
            using _t = void (DownloadItem::*)();
            if (_t _q_method = &DownloadItem::finished; *reinterpret_cast<_t *>(_a[1]) == _q_method) {
                *result = 1;
                return;
            }
        }
        {
            using _t = void (DownloadItem::*)(const QString & );
            if (_t _q_method = &DownloadItem::failed; *reinterpret_cast<_t *>(_a[1]) == _q_method) {
                *result = 2;
                return;
            }
        }
    }
}

const QMetaObject *DownloadItem::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *DownloadItem::qt_metacast(const char *_clname)
{
    if (!_clname) return nullptr;
    if (!strcmp(_clname, qt_meta_stringdata_DownloadItem.stringdata0))
        return static_cast<void*>(this);
    return QObject::qt_metacast(_clname);
}

int DownloadItem::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = QObject::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 6)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 6;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 6)
            *reinterpret_cast<QMetaType *>(_a[0]) = QMetaType();
        _id -= 6;
    }
    return _id;
}

// SIGNAL 0
void DownloadItem::progressChanged()
{
    QMetaObject::activate(this, &staticMetaObject, 0, nullptr);
}

// SIGNAL 1
void DownloadItem::finished()
{
    QMetaObject::activate(this, &staticMetaObject, 1, nullptr);
}

// SIGNAL 2
void DownloadItem::failed(const QString & _t1)
{
    void *_a[] = { nullptr, const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))) };
    QMetaObject::activate(this, &staticMetaObject, 2, _a);
}
namespace {
struct qt_meta_stringdata_DownloadManager_t {
    uint offsetsAndSizes[20];
    char stringdata0[16];
    char stringdata1[14];
    char stringdata2[1];
    char stringdata3[14];
    char stringdata4[5];
    char stringdata5[17];
    char stringdata6[15];
    char stringdata7[6];
    char stringdata8[19];
    char stringdata9[17];
};
#define QT_MOC_LITERAL(ofs, len) \
    uint(sizeof(qt_meta_stringdata_DownloadManager_t::offsetsAndSizes) + ofs), len 
Q_CONSTINIT static const qt_meta_stringdata_DownloadManager_t qt_meta_stringdata_DownloadManager = {
    {
        QT_MOC_LITERAL(0, 15),  // "DownloadManager"
        QT_MOC_LITERAL(16, 13),  // "downloadAdded"
        QT_MOC_LITERAL(30, 0),  // ""
        QT_MOC_LITERAL(31, 13),  // "DownloadItem*"
        QT_MOC_LITERAL(45, 4),  // "item"
        QT_MOC_LITERAL(50, 16),  // "downloadFinished"
        QT_MOC_LITERAL(67, 14),  // "downloadFailed"
        QT_MOC_LITERAL(82, 5),  // "error"
        QT_MOC_LITERAL(88, 18),  // "onDownloadFinished"
        QT_MOC_LITERAL(107, 16)   // "onDownloadFailed"
    },
    "DownloadManager",
    "downloadAdded",
    "",
    "DownloadItem*",
    "item",
    "downloadFinished",
    "downloadFailed",
    "error",
    "onDownloadFinished",
    "onDownloadFailed"
};
#undef QT_MOC_LITERAL
} // unnamed namespace

Q_CONSTINIT static const uint qt_meta_data_DownloadManager[] = {

 // content:
      10,       // revision
       0,       // classname
       0,    0, // classinfo
       5,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       3,       // signalCount

 // signals: name, argc, parameters, tag, flags, initial metatype offsets
       1,    1,   44,    2, 0x06,    1 /* Public */,
       5,    1,   47,    2, 0x06,    3 /* Public */,
       6,    2,   50,    2, 0x06,    5 /* Public */,

 // slots: name, argc, parameters, tag, flags, initial metatype offsets
       8,    0,   55,    2, 0x08,    8 /* Private */,
       9,    0,   56,    2, 0x08,    9 /* Private */,

 // signals: parameters
    QMetaType::Void, 0x80000000 | 3,    4,
    QMetaType::Void, 0x80000000 | 3,    4,
    QMetaType::Void, 0x80000000 | 3, QMetaType::QString,    4,    7,

 // slots: parameters
    QMetaType::Void,
    QMetaType::Void,

       0        // eod
};

Q_CONSTINIT const QMetaObject DownloadManager::staticMetaObject = { {
    QMetaObject::SuperData::link<QObject::staticMetaObject>(),
    qt_meta_stringdata_DownloadManager.offsetsAndSizes,
    qt_meta_data_DownloadManager,
    qt_static_metacall,
    nullptr,
    qt_incomplete_metaTypeArray<qt_meta_stringdata_DownloadManager_t,
        // Q_OBJECT / Q_GADGET
        QtPrivate::TypeAndForceComplete<DownloadManager, std::true_type>,
        // method 'downloadAdded'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        QtPrivate::TypeAndForceComplete<DownloadItem *, std::false_type>,
        // method 'downloadFinished'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        QtPrivate::TypeAndForceComplete<DownloadItem *, std::false_type>,
        // method 'downloadFailed'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        QtPrivate::TypeAndForceComplete<DownloadItem *, std::false_type>,
        QtPrivate::TypeAndForceComplete<const QString &, std::false_type>,
        // method 'onDownloadFinished'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'onDownloadFailed'
        QtPrivate::TypeAndForceComplete<void, std::false_type>
    >,
    nullptr
} };

void DownloadManager::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        auto *_t = static_cast<DownloadManager *>(_o);
        (void)_t;
        switch (_id) {
        case 0: _t->downloadAdded((*reinterpret_cast< std::add_pointer_t<DownloadItem*>>(_a[1]))); break;
        case 1: _t->downloadFinished((*reinterpret_cast< std::add_pointer_t<DownloadItem*>>(_a[1]))); break;
        case 2: _t->downloadFailed((*reinterpret_cast< std::add_pointer_t<DownloadItem*>>(_a[1])),(*reinterpret_cast< std::add_pointer_t<QString>>(_a[2]))); break;
        case 3: _t->onDownloadFinished(); break;
        case 4: _t->onDownloadFailed(); break;
        default: ;
        }
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        switch (_id) {
        default: *reinterpret_cast<QMetaType *>(_a[0]) = QMetaType(); break;
        case 0:
            switch (*reinterpret_cast<int*>(_a[1])) {
            default: *reinterpret_cast<QMetaType *>(_a[0]) = QMetaType(); break;
            case 0:
                *reinterpret_cast<QMetaType *>(_a[0]) = QMetaType::fromType< DownloadItem* >(); break;
            }
            break;
        case 1:
            switch (*reinterpret_cast<int*>(_a[1])) {
            default: *reinterpret_cast<QMetaType *>(_a[0]) = QMetaType(); break;
            case 0:
                *reinterpret_cast<QMetaType *>(_a[0]) = QMetaType::fromType< DownloadItem* >(); break;
            }
            break;
        case 2:
            switch (*reinterpret_cast<int*>(_a[1])) {
            default: *reinterpret_cast<QMetaType *>(_a[0]) = QMetaType(); break;
            case 0:
                *reinterpret_cast<QMetaType *>(_a[0]) = QMetaType::fromType< DownloadItem* >(); break;
            }
            break;
        }
    } else if (_c == QMetaObject::IndexOfMethod) {
        int *result = reinterpret_cast<int *>(_a[0]);
        {
            using _t = void (DownloadManager::*)(DownloadItem * );
            if (_t _q_method = &DownloadManager::downloadAdded; *reinterpret_cast<_t *>(_a[1]) == _q_method) {
                *result = 0;
                return;
            }
        }
        {
            using _t = void (DownloadManager::*)(DownloadItem * );
            if (_t _q_method = &DownloadManager::downloadFinished; *reinterpret_cast<_t *>(_a[1]) == _q_method) {
                *result = 1;
                return;
            }
        }
        {
            using _t = void (DownloadManager::*)(DownloadItem * , const QString & );
            if (_t _q_method = &DownloadManager::downloadFailed; *reinterpret_cast<_t *>(_a[1]) == _q_method) {
                *result = 2;
                return;
            }
        }
    }
}

const QMetaObject *DownloadManager::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *DownloadManager::qt_metacast(const char *_clname)
{
    if (!_clname) return nullptr;
    if (!strcmp(_clname, qt_meta_stringdata_DownloadManager.stringdata0))
        return static_cast<void*>(this);
    return QObject::qt_metacast(_clname);
}

int DownloadManager::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = QObject::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 5)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 5;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 5)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 5;
    }
    return _id;
}

// SIGNAL 0
void DownloadManager::downloadAdded(DownloadItem * _t1)
{
    void *_a[] = { nullptr, const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))) };
    QMetaObject::activate(this, &staticMetaObject, 0, _a);
}

// SIGNAL 1
void DownloadManager::downloadFinished(DownloadItem * _t1)
{
    void *_a[] = { nullptr, const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))) };
    QMetaObject::activate(this, &staticMetaObject, 1, _a);
}

// SIGNAL 2
void DownloadManager::downloadFailed(DownloadItem * _t1, const QString & _t2)
{
    void *_a[] = { nullptr, const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t2))) };
    QMetaObject::activate(this, &staticMetaObject, 2, _a);
}
QT_WARNING_POP
QT_END_MOC_NAMESPACE
