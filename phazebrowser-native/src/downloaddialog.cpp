#include "downloaddialog.h"
#include "downloadmanager.h"
#include <QHeaderView>
#include <QFileInfo>
#include <QDesktopServices>
#include <QUrl>
#include <QMessageBox>
#include <QDir>
#include <QMap>

DownloadDialog::DownloadDialog(DownloadManager *manager, QWidget *parent)
    : QDialog(parent)
    , downloadManager(manager)
{
    setWindowTitle("Downloads");
    setMinimumSize(700, 500);
    setupUI();
    
    // Load existing downloads
    QList<DownloadItem*> downloads = downloadManager->downloads();
    for (DownloadItem *item : downloads) {
        if (item) {
            onDownloadAdded(item);
        }
    }
    
    // Connect signals
    connect(downloadManager, &DownloadManager::downloadAdded, this, &DownloadDialog::onDownloadAdded);
    connect(downloadManager, &DownloadManager::downloadFinished, this, &DownloadDialog::onDownloadFinished);
}

void DownloadDialog::setupUI()
{
    QVBoxLayout *mainLayout = new QVBoxLayout(this);
    
    // Downloads table
    downloadsTable = new QTableWidget(this);
    downloadsTable->setColumnCount(5);
    downloadsTable->setHorizontalHeaderLabels(QStringList() << "File" << "Progress" << "Speed" << "Status" << "Actions");
    downloadsTable->horizontalHeader()->setStretchLastSection(true);
    downloadsTable->setSelectionBehavior(QAbstractItemView::SelectRows);
    downloadsTable->setSelectionMode(QAbstractItemView::SingleSelection);
    downloadsTable->setEditTriggers(QAbstractItemView::NoEditTriggers);
    downloadsTable->setStyleSheet(
        "QTableWidget { background: #1e1e1e; color: white; gridline-color: #404040; }"
        "QTableWidget::item { padding: 8px; }"
        "QHeaderView::section { background: #2d2d2d; color: white; padding: 8px; }"
    );
    
    mainLayout->addWidget(downloadsTable);
    
    // Buttons
    QHBoxLayout *buttonLayout = new QHBoxLayout();
    
    pauseResumeBtn = new QPushButton("Pause", this);
    pauseResumeBtn->setEnabled(false);
    connect(pauseResumeBtn, &QPushButton::clicked, this, &DownloadDialog::onPauseResume);
    buttonLayout->addWidget(pauseResumeBtn);
    
    cancelBtn = new QPushButton("Cancel", this);
    cancelBtn->setEnabled(false);
    connect(cancelBtn, &QPushButton::clicked, this, &DownloadDialog::onCancel);
    buttonLayout->addWidget(cancelBtn);
    
    openFolderBtn = new QPushButton("Open Folder", this);
    connect(openFolderBtn, &QPushButton::clicked, this, &DownloadDialog::onOpenFolder);
    buttonLayout->addWidget(openFolderBtn);
    
    buttonLayout->addStretch();
    
    clearHistoryBtn = new QPushButton("Clear History", this);
    connect(clearHistoryBtn, &QPushButton::clicked, this, &DownloadDialog::onClearHistory);
    buttonLayout->addWidget(clearHistoryBtn);
    
    closeBtn = new QPushButton("Close", this);
    connect(closeBtn, &QPushButton::clicked, this, &QDialog::accept);
    buttonLayout->addWidget(closeBtn);
    
    mainLayout->addLayout(buttonLayout);
    
    // Connect table selection
    connect(downloadsTable, &QTableWidget::itemSelectionChanged, [this]() {
        bool hasSelection = downloadsTable->selectedItems().size() > 0;
        pauseResumeBtn->setEnabled(hasSelection);
        cancelBtn->setEnabled(hasSelection);
    });
}

void DownloadDialog::onDownloadAdded(DownloadItem *item)
{
    int row = downloadsTable->rowCount();
    downloadsTable->insertRow(row);
    
    itemToRow[item] = row;
    
    // File name
    downloadsTable->setItem(row, 0, new QTableWidgetItem(item->filename()));
    
    // Progress bar
    QProgressBar *progressBar = new QProgressBar();
    progressBar->setRange(0, 100);
    progressBar->setValue(0);
    progressBar->setTextVisible(true);
    progressBar->setStyleSheet(
        "QProgressBar { border: 1px solid #404040; border-radius: 4px; text-align: center; }"
        "QProgressBar::chunk { background: #0078d4; }"
    );
    downloadsTable->setCellWidget(row, 1, progressBar);
    
    // Speed
    downloadsTable->setItem(row, 2, new QTableWidgetItem("—"));
    
    // Status
    downloadsTable->setItem(row, 3, new QTableWidgetItem("Downloading..."));
    
    // Actions (placeholder)
    downloadsTable->setItem(row, 4, new QTableWidgetItem(""));
    
    // Connect progress updates
    connect(item, &DownloadItem::progressChanged, this, &DownloadDialog::onDownloadProgress);
    
    updateDownloadRow(row, item);
}

void DownloadDialog::onDownloadFinished(DownloadItem *item)
{
    int row = findDownloadRow(item);
    if (row >= 0) {
        updateDownloadRow(row, item);
        downloadsTable->item(row, 3)->setText("Completed");
    }
}

void DownloadDialog::onDownloadProgress()
{
    DownloadItem *item = qobject_cast<DownloadItem*>(sender());
    if (item) {
        int row = findDownloadRow(item);
        if (row >= 0) {
            updateDownloadRow(row, item);
        }
    }
}

void DownloadDialog::updateDownloadRow(int row, DownloadItem *item)
{
    if (row < 0 || row >= downloadsTable->rowCount()) return;
    
    // Update progress bar
    QProgressBar *progressBar = qobject_cast<QProgressBar*>(downloadsTable->cellWidget(row, 1));
    if (progressBar) {
        int progress = static_cast<int>(item->progress() * 100);
        progressBar->setValue(progress);
        progressBar->setFormat(QString("%1%").arg(progress));
    }
    
    // Update status
    if (item->isFinished()) {
        downloadsTable->item(row, 3)->setText("Completed");
    } else if (item->isPaused()) {
        downloadsTable->item(row, 3)->setText("Paused");
    } else {
        downloadsTable->item(row, 3)->setText("Downloading...");
    }
}

int DownloadDialog::findDownloadRow(DownloadItem *item)
{
    return itemToRow.value(item, -1);
}

void DownloadDialog::onPauseResume()
{
    int row = downloadsTable->currentRow();
    if (row >= 0) {
        DownloadItem *item = nullptr;
        for (auto it = itemToRow.begin(); it != itemToRow.end(); ++it) {
            if (it.value() == row) {
                item = it.key();
                break;
            }
        }
        if (item) {
            if (item->isPaused()) {
                item->resume();
                pauseResumeBtn->setText("Pause");
            } else {
                item->pause();
                pauseResumeBtn->setText("Resume");
            }
            updateDownloadRow(row, item);
        }
    }
}

void DownloadDialog::onCancel()
{
    int row = downloadsTable->currentRow();
    if (row >= 0) {
        DownloadItem *item = nullptr;
        for (auto it = itemToRow.begin(); it != itemToRow.end(); ++it) {
            if (it.value() == row) {
                item = it.key();
                break;
            }
        }
        if (item) {
            item->cancel();
            downloadsTable->item(row, 3)->setText("Cancelled");
        }
    }
}

void DownloadDialog::onOpenFolder()
{
    QString downloadPath = downloadManager->defaultDownloadPath();
    QDesktopServices::openUrl(QUrl::fromLocalFile(downloadPath));
}

void DownloadDialog::onClearHistory()
{
    int ret = QMessageBox::question(this, "Clear History", "Are you sure you want to clear download history?");
    if (ret == QMessageBox::Yes) {
        downloadManager->clearHistory();
    }
}
