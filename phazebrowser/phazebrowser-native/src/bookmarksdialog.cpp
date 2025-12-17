#include "bookmarksdialog.h"
#include "datamanager.h"
#include <QInputDialog>
#include <QMessageBox>
#include <QTreeWidgetItem>
#include <QHeaderView>

BookmarksDialog::BookmarksDialog(DataManager *dataManager, QWidget *parent)
    : QDialog(parent)
    , dataManager(dataManager)
{
    setWindowTitle("Bookmarks");
    setMinimumSize(600, 500);
    setupUI();
    loadBookmarks();
}

void BookmarksDialog::setupUI()
{
    QVBoxLayout *mainLayout = new QVBoxLayout(this);
    
    // Search box
    searchBox = new QLineEdit(this);
    searchBox->setPlaceholderText("Search bookmarks...");
    searchBox->setStyleSheet("padding: 6px 12px; background: #3d3d3d; border: 1px solid #404040; border-radius: 4px;");
    connect(searchBox, &QLineEdit::textChanged, this, &BookmarksDialog::onSearchBookmarks);
    mainLayout->addWidget(searchBox);
    
    // Bookmarks tree
    bookmarksTree = new QTreeWidget(this);
    bookmarksTree->setHeaderLabels(QStringList() << "Name" << "URL");
    bookmarksTree->setColumnCount(2);
    bookmarksTree->header()->setStretchLastSection(true);
    bookmarksTree->setSelectionMode(QAbstractItemView::SingleSelection);
    bookmarksTree->setStyleSheet(
        "QTreeWidget { background: #1e1e1e; color: white; }"
        "QTreeWidget::item { padding: 4px; }"
        "QTreeWidget::item:selected { background: #0078d4; }"
        "QHeaderView::section { background: #2d2d2d; color: white; padding: 8px; }"
    );
    
    mainLayout->addWidget(bookmarksTree);
    
    // Buttons
    QHBoxLayout *buttonLayout = new QHBoxLayout();
    
    addBtn = new QPushButton("➕ Add");
    connect(addBtn, &QPushButton::clicked, this, &BookmarksDialog::onAddBookmark);
    buttonLayout->addWidget(addBtn);
    
    editBtn = new QPushButton("✏️ Edit");
    editBtn->setEnabled(false);
    connect(editBtn, &QPushButton::clicked, this, &BookmarksDialog::onEditBookmark);
    buttonLayout->addWidget(editBtn);
    
    deleteBtn = new QPushButton("🗑️ Delete");
    deleteBtn->setEnabled(false);
    connect(deleteBtn, &QPushButton::clicked, this, &BookmarksDialog::onDeleteBookmark);
    buttonLayout->addWidget(deleteBtn);
    
    addFolderBtn = new QPushButton("📁 Add Folder");
    connect(addFolderBtn, &QPushButton::clicked, this, &BookmarksDialog::onAddFolder);
    buttonLayout->addWidget(addFolderBtn);
    
    buttonLayout->addStretch();
    
    QPushButton *closeBtn = new QPushButton("Close");
    connect(closeBtn, &QPushButton::clicked, this, &QDialog::accept);
    buttonLayout->addWidget(closeBtn);
    
    mainLayout->addLayout(buttonLayout);
    
    // Connect selection
    connect(bookmarksTree, &QTreeWidget::itemSelectionChanged, [this]() {
        bool hasSelection = bookmarksTree->selectedItems().size() > 0;
        editBtn->setEnabled(hasSelection);
        deleteBtn->setEnabled(hasSelection);
    });
    
    // Connect double-click
    connect(bookmarksTree, &QTreeWidget::itemDoubleClicked, this, &BookmarksDialog::onItemDoubleClicked);
}

void BookmarksDialog::onItemDoubleClicked(QTreeWidgetItem *item, int column)
{
    Q_UNUSED(column);
    QString url = item->data(0, Qt::UserRole).toString();
    if (!url.isEmpty()) {
        emit urlSelected(QUrl(url));
        accept();
    }
}

void BookmarksDialog::loadBookmarks()
{
    updateTree();
}

void BookmarksDialog::updateTree()
{
    bookmarksTree->clear();
    
    QJsonArray bookmarks = dataManager->getBookmarks();
    for (const QJsonValue &value : bookmarks) {
        QJsonObject bookmark = value.toObject();
        QTreeWidgetItem *item = new QTreeWidgetItem(bookmarksTree);
        item->setText(0, bookmark["title"].toString());
        item->setText(1, bookmark["url"].toString());
        item->setData(0, Qt::UserRole, bookmark["url"].toString());
    }
}

void BookmarksDialog::onAddBookmark()
{
    QString url = QInputDialog::getText(this, "Add Bookmark", "URL:");
    QString title = QInputDialog::getText(this, "Add Bookmark", "Title:");
    
    if (!url.isEmpty()) {
        if (title.isEmpty()) title = url;
        dataManager->addBookmark(url, title);
        updateTree();
    }
}

void BookmarksDialog::onEditBookmark()
{
    QTreeWidgetItem *item = bookmarksTree->currentItem();
    if (item) {
        QString oldUrl = item->data(0, Qt::UserRole).toString();
        QString url = QInputDialog::getText(this, "Edit Bookmark", "URL:", QLineEdit::Normal, oldUrl);
        QString title = QInputDialog::getText(this, "Edit Bookmark", "Title:", QLineEdit::Normal, item->text(0));
        
        if (!url.isEmpty()) {
            dataManager->removeBookmark(oldUrl);
            dataManager->addBookmark(url, title.isEmpty() ? url : title);
            updateTree();
        }
    }
}

void BookmarksDialog::onDeleteBookmark()
{
    QTreeWidgetItem *item = bookmarksTree->currentItem();
    if (item) {
        QString url = item->data(0, Qt::UserRole).toString();
        int ret = QMessageBox::question(this, "Delete Bookmark", "Are you sure you want to delete this bookmark?");
        if (ret == QMessageBox::Yes) {
            dataManager->removeBookmark(url);
            updateTree();
        }
    }
}

void BookmarksDialog::onAddFolder()
{
    QString folderName = QInputDialog::getText(this, "Add Folder", "Folder Name:");
    if (!folderName.isEmpty()) {
        QTreeWidgetItem *folder = new QTreeWidgetItem(bookmarksTree);
        folder->setText(0, folderName);
        folder->setIcon(0, QIcon::fromTheme("folder"));
    }
}

void BookmarksDialog::onSearchBookmarks(const QString &text)
{
    // TODO: Filter bookmarks by search text
    Q_UNUSED(text);
}
