/****************************************************************************
** Meta object code from reading C++ file 'bookmarksdialog.h'
**
** Created by: The Qt Meta Object Compiler version 68 (Qt 6.4.2)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include <memory>
#include "../../../src/bookmarksdialog.h"
#include <QtGui/qtextcursor.h>
#include <QtCore/qmetatype.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'bookmarksdialog.h' doesn't include <QObject>."
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
struct qt_meta_stringdata_BookmarksDialog_t {
    uint offsetsAndSizes[28];
    char stringdata0[16];
    char stringdata1[12];
    char stringdata2[1];
    char stringdata3[4];
    char stringdata4[14];
    char stringdata5[15];
    char stringdata6[17];
    char stringdata7[12];
    char stringdata8[18];
    char stringdata9[5];
    char stringdata10[20];
    char stringdata11[17];
    char stringdata12[5];
    char stringdata13[7];
};
#define QT_MOC_LITERAL(ofs, len) \
    uint(sizeof(qt_meta_stringdata_BookmarksDialog_t::offsetsAndSizes) + ofs), len 
Q_CONSTINIT static const qt_meta_stringdata_BookmarksDialog_t qt_meta_stringdata_BookmarksDialog = {
    {
        QT_MOC_LITERAL(0, 15),  // "BookmarksDialog"
        QT_MOC_LITERAL(16, 11),  // "urlSelected"
        QT_MOC_LITERAL(28, 0),  // ""
        QT_MOC_LITERAL(29, 3),  // "url"
        QT_MOC_LITERAL(33, 13),  // "onAddBookmark"
        QT_MOC_LITERAL(47, 14),  // "onEditBookmark"
        QT_MOC_LITERAL(62, 16),  // "onDeleteBookmark"
        QT_MOC_LITERAL(79, 11),  // "onAddFolder"
        QT_MOC_LITERAL(91, 17),  // "onSearchBookmarks"
        QT_MOC_LITERAL(109, 4),  // "text"
        QT_MOC_LITERAL(114, 19),  // "onItemDoubleClicked"
        QT_MOC_LITERAL(134, 16),  // "QTreeWidgetItem*"
        QT_MOC_LITERAL(151, 4),  // "item"
        QT_MOC_LITERAL(156, 6)   // "column"
    },
    "BookmarksDialog",
    "urlSelected",
    "",
    "url",
    "onAddBookmark",
    "onEditBookmark",
    "onDeleteBookmark",
    "onAddFolder",
    "onSearchBookmarks",
    "text",
    "onItemDoubleClicked",
    "QTreeWidgetItem*",
    "item",
    "column"
};
#undef QT_MOC_LITERAL
} // unnamed namespace

Q_CONSTINIT static const uint qt_meta_data_BookmarksDialog[] = {

 // content:
      10,       // revision
       0,       // classname
       0,    0, // classinfo
       7,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       1,       // signalCount

 // signals: name, argc, parameters, tag, flags, initial metatype offsets
       1,    1,   56,    2, 0x06,    1 /* Public */,

 // slots: name, argc, parameters, tag, flags, initial metatype offsets
       4,    0,   59,    2, 0x08,    3 /* Private */,
       5,    0,   60,    2, 0x08,    4 /* Private */,
       6,    0,   61,    2, 0x08,    5 /* Private */,
       7,    0,   62,    2, 0x08,    6 /* Private */,
       8,    1,   63,    2, 0x08,    7 /* Private */,
      10,    2,   66,    2, 0x08,    9 /* Private */,

 // signals: parameters
    QMetaType::Void, QMetaType::QUrl,    3,

 // slots: parameters
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, QMetaType::QString,    9,
    QMetaType::Void, 0x80000000 | 11, QMetaType::Int,   12,   13,

       0        // eod
};

Q_CONSTINIT const QMetaObject BookmarksDialog::staticMetaObject = { {
    QMetaObject::SuperData::link<QDialog::staticMetaObject>(),
    qt_meta_stringdata_BookmarksDialog.offsetsAndSizes,
    qt_meta_data_BookmarksDialog,
    qt_static_metacall,
    nullptr,
    qt_incomplete_metaTypeArray<qt_meta_stringdata_BookmarksDialog_t,
        // Q_OBJECT / Q_GADGET
        QtPrivate::TypeAndForceComplete<BookmarksDialog, std::true_type>,
        // method 'urlSelected'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        QtPrivate::TypeAndForceComplete<const QUrl &, std::false_type>,
        // method 'onAddBookmark'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'onEditBookmark'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'onDeleteBookmark'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'onAddFolder'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'onSearchBookmarks'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        QtPrivate::TypeAndForceComplete<const QString &, std::false_type>,
        // method 'onItemDoubleClicked'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        QtPrivate::TypeAndForceComplete<QTreeWidgetItem *, std::false_type>,
        QtPrivate::TypeAndForceComplete<int, std::false_type>
    >,
    nullptr
} };

void BookmarksDialog::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        auto *_t = static_cast<BookmarksDialog *>(_o);
        (void)_t;
        switch (_id) {
        case 0: _t->urlSelected((*reinterpret_cast< std::add_pointer_t<QUrl>>(_a[1]))); break;
        case 1: _t->onAddBookmark(); break;
        case 2: _t->onEditBookmark(); break;
        case 3: _t->onDeleteBookmark(); break;
        case 4: _t->onAddFolder(); break;
        case 5: _t->onSearchBookmarks((*reinterpret_cast< std::add_pointer_t<QString>>(_a[1]))); break;
        case 6: _t->onItemDoubleClicked((*reinterpret_cast< std::add_pointer_t<QTreeWidgetItem*>>(_a[1])),(*reinterpret_cast< std::add_pointer_t<int>>(_a[2]))); break;
        default: ;
        }
    } else if (_c == QMetaObject::IndexOfMethod) {
        int *result = reinterpret_cast<int *>(_a[0]);
        {
            using _t = void (BookmarksDialog::*)(const QUrl & );
            if (_t _q_method = &BookmarksDialog::urlSelected; *reinterpret_cast<_t *>(_a[1]) == _q_method) {
                *result = 0;
                return;
            }
        }
    }
}

const QMetaObject *BookmarksDialog::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *BookmarksDialog::qt_metacast(const char *_clname)
{
    if (!_clname) return nullptr;
    if (!strcmp(_clname, qt_meta_stringdata_BookmarksDialog.stringdata0))
        return static_cast<void*>(this);
    return QDialog::qt_metacast(_clname);
}

int BookmarksDialog::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = QDialog::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 7)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 7;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 7)
            *reinterpret_cast<QMetaType *>(_a[0]) = QMetaType();
        _id -= 7;
    }
    return _id;
}

// SIGNAL 0
void BookmarksDialog::urlSelected(const QUrl & _t1)
{
    void *_a[] = { nullptr, const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))) };
    QMetaObject::activate(this, &staticMetaObject, 0, _a);
}
QT_WARNING_POP
QT_END_MOC_NAMESPACE
