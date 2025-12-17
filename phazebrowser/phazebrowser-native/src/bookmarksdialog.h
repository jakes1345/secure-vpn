#ifndef BOOKMARKSDIALOG_H
#define BOOKMARKSDIALOG_H

#include <QDialog>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QTreeWidget>
#include <QPushButton>
#include <QLineEdit>
#include <QLabel>
#include "datamanager.h"

class BookmarksDialog : public QDialog
{
    Q_OBJECT

public:
    explicit BookmarksDialog(DataManager *dataManager, QWidget *parent = nullptr);

private slots:
    void onAddBookmark();
    void onEditBookmark();
    void onDeleteBookmark();
    void onAddFolder();
    void onSearchBookmarks(const QString &text);
    void onItemDoubleClicked(QTreeWidgetItem *item, int column);

signals:
    void urlSelected(const QUrl &url);

private:
    void setupUI();
    void loadBookmarks();
    void updateTree();
    
    DataManager *dataManager;
    QTreeWidget *bookmarksTree;
    QLineEdit *searchBox;
    QPushButton *addBtn;
    QPushButton *editBtn;
    QPushButton *deleteBtn;
    QPushButton *addFolderBtn;
};

#endif // BOOKMARKSDIALOG_H
