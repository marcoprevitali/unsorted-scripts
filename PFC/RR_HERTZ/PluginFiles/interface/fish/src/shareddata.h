#pragma once

// Basically duplicates QSharedData, QSharedPointer
// but allows the option of deferring deletion to the utility thread so
//   massively nested data structures do not crash the code on destruction.
// Also allows restoration of sharing on save/restore, which
//   otherwise is lost and can occasionally cause massive memory use
//   increases on restore when there is lots of implicit sharing of large
//   data types (matrices, arrays, lists, etc).
// The DELETION enumeration template parameter controls whether
//   deletion should be deferred to the utility thread
//   (for heirarchical types like LIST, MAP, STRUCT) or immediately
//   (for large shared but not heirarchical types like MATRIX).

#include "savedepth.h"
#include "utilitythread.h"
#include "shared/src/archive2.h"

namespace fish {
    template <class T>
    class SharedData {
    public:
        SharedData() {}
        SharedData(const SharedData &) { }

        void ref() { ++ref_;  }
        bool deref() { return --ref_ != 0; }
        bool unique() const { return ref_.load()==1;  }

        void saveShared(itasca::Archive2 &a) const;
        T *restoreShared(itasca::Archive2 &a);
        void remapShared(itasca::Archive2 &a); // Returns TRUE if remap should be skipped!

        virtual T *      getT() = 0;
        virtual const T *getT() const = 0;
        virtual void     save(itasca::Archive2 &) const = 0;
        virtual void     restore(itasca::Archive2 &) = 0;
        virtual void     remap(itasca::Archive2 &) = 0;

    private:
        struct StaticData {
            std::unordered_map<quint64, T *> idMap_;
            quint32 mapArchiveInstance_{0};
        };
        static StaticData staticData_;

        std::atomic<qint32> ref_{0};

        mutable quint64 id_{0};
        mutable quint32 archiveInstance_{0};
        mutable quint32 remapInstance_{0};
    };

    enum class DeleteHandling { Immediate, Deferred };
    template <class T,DeleteHandling DELTYP>
    class SharedDataPointer {
    public:
        SharedDataPointer() {};
        ~SharedDataPointer() { if (d_ && !d_->deref()) deleteHelper(); }
        explicit SharedDataPointer(T *data) noexcept : d_(data) { if (d_) d_->ref();  }
        SharedDataPointer(const SharedDataPointer<T,DELTYP> &o) : d_(o.d_) { if (d_) d_->ref(); }
        SharedDataPointer(SharedDataPointer<T,DELTYP> &&o) noexcept : d_(o.d_) { o.d_ = nullptr; }

        SharedDataPointer<T,DELTYP> &operator=(const SharedDataPointer<T,DELTYP> &o);
        SharedDataPointer<T,DELTYP> &operator=(T *o);
        SharedDataPointer<T,DELTYP> &operator=(SharedDataPointer<T,DELTYP> &&other) noexcept;

        bool operator==(const SharedDataPointer<T,DELTYP> &other) const { return d_ == other.d_; }
        bool operator!=(const SharedDataPointer<T,DELTYP> &other) const { return d_ != other.d_; }
        bool operator!() const { return !d_; }

        operator T *() { detach(); return d_; }
        operator const T *() const { return d_; }

        T &      operator*() { detach(); return *d_; }
        const T &operator*() const { return *d_; }
        T *      operator->() { detach(); return d_; }
        const T *operator->() const { return d_; }

        T *data() { detach(); return d_; }
        const T *data() const { return d_; }
        const T *constData() const { return d_; }

        void swap(SharedDataPointer &other) noexcept { std::swap(d_, other.d_); }
        void detach() { if (d_ && !d_->unique()) detachHelper(); }

        void save(itasca::Archive2 &a) const;
        bool restore(itasca::Archive2 &a,quint64 label);
        void remap(itasca::Archive2 &a);

    private:
        void deleteHelper();
        void detachHelper();

        quint64 id_{0};
        T *d_{nullptr};
    };

    template <class T>
    void SharedData<T>::saveShared(itasca::Archive2 &a) const {
        struct SharedDataSave {};
        a.startObjectSave(typeid(SharedDataSave));
        if (staticData_.mapArchiveInstance_!=a.instance()) 
            staticData_.idMap_.clear();
        staticData_.mapArchiveInstance_ = a.instance();
        if (archiveInstance_!=a.instance()) 
            id_ = 0;
        archiveInstance_ = a.instance();
        bool saveThisOne = false;
        if (id_==0) {
            id_ = staticData_.idMap_.size() + 1;
            staticData_.idMap_[id_] = const_cast<T *>(getT());
            saveThisOne = true;
        }
        a.save("ID", id_);
        a.saveLabel("Array");
        a.startArraySave(saveThisOne ? 1 : 0, itasca::Archive2::Type::Object);
            if (saveThisOne) {
                struct SharedDataSave2 {};
                a.startObjectSave(typeid(SharedDataSave2));
                    a.saveLabel("Value");
                    save(a);
                a.stopObjectSave();
            }
        a.stopArray();
        a.stopObjectSave();

    }

    template <class T>
    T *SharedData<T>::restoreShared(itasca::Archive2 &a) {
        using itasca::enc;

        if (staticData_.mapArchiveInstance_!=a.instance())
            staticData_.idMap_.clear();
        staticData_.mapArchiveInstance_ = a.instance();
        T *ret = getT();
        a.startObjectRestore();
        for (quint64 label=a.restoreLabel();label!=itasca::Archive2::finish_;label=a.restoreLabel()) {
            switch (label) {
            case enc("ID"): {
                    a.restore(id_);
                    auto it = staticData_.idMap_.find(id_);
                    if (it!=staticData_.idMap_.end())
                        ret = it->second;
                }
                break;
            case enc("Array"):  
                a.startArrayRestore();
                while (a.checkArray()) {
                    a.startObjectRestore();
                    for (quint64 label2 = a.restoreLabel(); label2!=itasca::Archive2::finish_;label2 = a.restoreLabel()) {
                        switch (label2) {
                        case enc("Value"):  
                            staticData_.idMap_[id_] = getT(); // WARNING
                            assert(ret==this);
                            restore(a);
                            break;
                        default:   a.skipValue();   break;
                        }
                        
                    }
                    a.stopObjectRestore();
                }
                break;
            }
        }
        a.stopObjectRestore();
        return ret;
    }

    template <class T>
    void SharedData<T>::remapShared(itasca::Archive2 &a) {
        if (remapInstance_==a.instance()) return;
        remapInstance_ = a.instance();
        remap(a);
    }

    template <class T,DeleteHandling DELTYP>
    SharedDataPointer<T,DELTYP> &SharedDataPointer<T,DELTYP>::operator=(const SharedDataPointer<T,DELTYP> &o) {
        if (o.d_ != d_) {
            if (o.d_)
                o.d_->ref();
            if (d_ && !d_->deref())
                deleteHelper();
            d_ = o.d_;
        }
        return *this;
    }

    template <class T,DeleteHandling DELTYP>
    SharedDataPointer<T,DELTYP> &SharedDataPointer<T,DELTYP>::operator=(T *o) {
        if (o != d_) {
            if (o)
                o->ref();
            if (d_ && !d_->deref())
                deleteHelper();
            d_ = o;
        }
        return *this;
    }

    template <class T,DeleteHandling DELTYP>
    SharedDataPointer<T,DELTYP> &SharedDataPointer<T,DELTYP>::operator=(SharedDataPointer<T,DELTYP> &&other) noexcept {
        SharedDataPointer moved(std::move(other));
        swap(moved);
        return *this;
    }

    template <class T,DeleteHandling DELTYP>
    void SharedDataPointer<T,DELTYP>::save(itasca::Archive2 &a) const {
        if (SaveDepth::depth(a.instance())>SaveDepth::limit_)
            throw Exception("FISH LIST type nest level too high (larger than %1)."
                " This type does not allow this level of nesting.",SaveDepth::limit_);
        assert(d_);
        a.saveLabel("Base");
        d_->saveShared(a);
    }

    template <class T,DeleteHandling DELTYP>
    bool SharedDataPointer<T,DELTYP>::restore(itasca::Archive2 &a,quint64 label) {
        switch (label) {
        case itasca::enc("Base"): operator=(d_->restoreShared(a));  return true;
        }
        return false;
    }

    template <class T,DeleteHandling DELTYP>
    void SharedDataPointer<T,DELTYP>::remap(itasca::Archive2 &a) {
        d_->remapShared(a);
    }


    template <class T,DeleteHandling DELTYP>
    void SharedDataPointer<T,DELTYP>::detachHelper() {
        T *x = new T(*d_);
        x->ref();
        if (!d_->deref())
            deleteHelper();
        d_ = x;
    }

    template <class T,DeleteHandling DELTYP>
    void SharedDataPointer<T,DELTYP>::deleteHelper() {
        auto *pnt = d_;
        if constexpr (DELTYP==DeleteHandling::Immediate)
            delete pnt;
        else
            UtilityThread::instance()->execute([pnt] { delete pnt; });
    }
} // namespace fish
// EoF
