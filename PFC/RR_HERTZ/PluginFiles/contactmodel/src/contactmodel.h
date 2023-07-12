#pragma once
// contactmodel.h

#include "contactmodel/interface/icontactmodel.h"
#include "contactmodel_global.h"

#include "base/src/farray.h"
#include "shared/src/archivestream.h"
// contactmodel.h
/** \brief Contact model class.
    * \file contactmodel.h
    *
    * \addtogroup contactmodel Contact model implementation
*/

#if DIM==2
    #define cmodelsxd cmodels2d
#else
    #define cmodelsxd cmodels3d
#endif

#pragma warning(push)
#pragma warning(disable:4251)

namespace itasca {
    class IProgram;
}


namespace cmodelsxd {
    using namespace itasca;
    using namespace itascaxd;
    class ContactModelState;
    
    static const quint32 ACTIVE_IS      = 0x000001;  /* active      */
    static const quint32 ACTIVATED      = 0x000002;  /* activated   */
    static const quint32 ACTIVE_COULDBE = 0x000004;  /* could be    */
    
    /** * \brief 
      * The ContactModelState class holds necessary information to communicate back and forth between the code (e.g., <em>PFC</em>) and the contact model.
      * \ingroup contactmodel
      */
    class ContactModelState {
    public:
        /// Constructor
        ContactModelState(): activeState_(0),trackEnergy_(false) { }
        /// Destructor
        virtual ~ContactModelState() {};
        /// Return a const pointer to the IPrgram interface
        virtual const IProgram *          getProgram() const=0;
        /// Set the activity state of the contact.  
        bool setActive(bool b=true) { if (b) activeState_ |= ACTIVE_IS; else activeState_ &=~ ACTIVE_IS; return isActive(); }
        /// Set the activity state of the contact.  
        bool setCouldBeActive(bool b=true) { if (b) activeState_ |= ACTIVE_COULDBE; else activeState_ &=~ ACTIVE_COULDBE; return couldBeActive(); }
        /// Set the activity state of the contact.  
        bool setActivated(bool b=true) { if (b) activeState_ |= ACTIVATED; else activeState_ &=~ ACTIVATED; return activated(); }
    
        /// Returns true if the contact state is active.  
        bool isActive() const  { return activeState_ & ACTIVE_IS; }
        /// Returns true if the contact state is inactive.  
        bool isInactive() const  { return !isActive(); }
        /// Returns true if the contact state is activated.  
        bool activated() const  { return activeState_ & ACTIVATED; }
        /// Returns true if the contact could be activate in subsequent steps.  
        bool couldBeActive() const { return activeState_ & ACTIVE_COULDBE; }
        quint32 activeState_;                      ///< Current activity state flag
        bool trackEnergy_;                         ///< indicate whether energy tracking is activated
    };
    
    /** * \brief 
      * Contact model implementation.
      * \ingroup contactmodel
      */
    class CONTACTMODEL_EXPORT ContactModel : public IContactModel
    {
    public:
        /// Constructor
        ContactModel();

        /// Destructor
        virtual ~ContactModel();
    
        /// Make a clone of this contact model. Must be implemeted. 
        virtual ContactModel *clone() const=0;
        
        /// Generic implementation - by default it is always OK to delete a contact.
        virtual bool          isOKToDelete() const { return true; }
        
        /// Used for save/restore. Important to implement.
        virtual void          archive(ArchiveStream &) {} 
        
        /// Copy the contact model from \a cm. Must be overridden in derived classes.
        virtual void          copy(const ContactModel *cm) { cmEvents_ = cm->cmEvents_; }
        
        // IContactModel functions.
        
        /// Return the IContactModel pointer.
        virtual IContactModel *       getContactModel() {return this;}
        
        /// Return the const IContactModel pointer.
        virtual const IContactModel * getContactModel() const {return this;}
        virtual QString               getName() const=0;
        
        /// By default, the plugin name is the contact model name. Must be implemented in derived class
        virtual QString               getPluginName() const { return getName(); }
        
        /// Returns a comma delimited string that lists the contact model properies. Must be implemented in derived classes.
        virtual QString               getProperties() const=0; // comma delimited

        /// Returns a QVariant corresponding to the property with position \a i in the string returned by getProperties().
        /// Must be implemented in derived classes.
        /// \param i Position index in the comma-delimited property list string.
        /// \param con Optional contact pointer. This pointer is null if the contact model instance is not assigned to any contact.
        virtual QVariant              getProperty(uint i,const IContact *con=0) const=0; 
 
        /// Returns a boolean indicating whether the property with a given index (see the getProperty() method description)
        /// is expressed in the global coordinate system or in the contact local coordinate system. This is important for vectors.
        /// Must be overridden in derived classes.
        virtual bool                  getPropertyGlobal(uint ) const {return true;}

        /// Returns the integer index of a property based on the property list returned by getProperties, starting at 1.
        /// This method overrides the IContactModel pure virtual method, and should not be overridden by derived classes. 
        virtual int                   isProperty(const QString &c,Qt::CaseSensitivity cs=Qt::CaseInsensitive) const;

        /// Set the value of the property at position \a i in the string returned by getProperties().
        /// Must be implemented in derived classes.
        /// \param i Position index in the comma-delimited property list string.
        /// \param v QVariant holding the value to be set.
        /// \param con Optional contact pointer. This pointer is null if the contact model instance is not assigned to any contact.
        virtual bool                  setProperty(uint i,const QVariant &v,IContact *con=0)=0;

        virtual bool                  getPropertyReadOnly(uint) const { return false; } // Base 1
        virtual bool                  supportsInheritance(uint) const { return false; } // Base 1
        virtual bool                  getInheritance(uint) const {return false;} 
        virtual void                  setInheritance(uint,bool) {}
    
        virtual QString               getMethods() const {return QString();}                                                      // comma delimited
        
        /// Processing of a methods based on the method list returned by getMehtods.
        virtual int                   isMethod(const QString &c,Qt::CaseSensitivity cs=Qt::CaseInsensitive) const;                // checks the list for a match, returns the integer (>0) if a match is found
        
        /// Default implementation so that no methods must be defined. 
        virtual QString               getMethodArguments(uint) const {return QString();}                                          // comma delimited
        
        /// By default, no methods must be defined. 
        virtual bool                  setMethod(uint,const QVector<QVariant> &,IContact*c=0) {c;return false;}                      // Base 1 - returns true if timestep contributions need to be updated
    
        /// Default implementation so that no energies must be defined. 
        virtual QString               getEnergies() const {return QString();}                                                     // comma delimited
        
        /// Default implementation so that no energies must be defined. 
        virtual int                   isEnergy(const QString &c,Qt::CaseSensitivity cs=Qt::CaseInsensitive) const;                // checks the list for a match, returns the integer (>0) if a match is found
        
        /// Default implementation so that no energies must be defined. 
        virtual double                getEnergy(uint ) const {return 0.0;}                                                        // Base 1
        
        /// Default implementation so that no energies must be defined. 
        virtual bool                  getEnergyAccumulate(uint ) const {return false;}                                            // Base 1
        
        /// Default implementation so that no energies must be defined. 
        virtual void                  setEnergy(uint ,const double &) {}                                                          // Base 1    
        
        /// Default implementation so that no energies must be defined. 
        virtual void                  activateEnergy() {}
        
        /// Default implementation so that no energies must be defined. 
        virtual bool                  getEnergyActivated() const {return false;}  // Returns a boolean indicating if energies have been instanciated
        
        virtual uint                  getMinorVersion() const=0;
        virtual void                  destroy() { delete this; }
    
        /// For contact specific plotting
        virtual void getSphereList(const IContact *con,std::vector<DVect> *pos,std::vector<double> *rad,std::vector<double> *val)=0;
#ifdef THREED
        /// For contact specific plotting
        virtual void getDiskList(const IContact *con,std::vector<DVect> *pos,std::vector<DVect> *normal,std::vector<double> *radius,std::vector<double> *val)=0;
#endif
        /// For contact specific plotting
        virtual void getCylinderList(const IContact *con,std::vector<DVect> *bot,std::vector<DVect> *top,std::vector<double> *radlow,std::vector<double> *radhi,std::vector<double> *val)=0;
        
        /// Return a comma delimited liest of FISH callback events. 
        virtual QString               getFishCallEvents() const {return QString();};         // comma delimited

        /// Set the order of the contact model events as stored in the ContactModelList.
        void                          setEventVal(int i,int j);
        
        /// For executing events within the contact model.
        void                          setFromParent(const ContactModel *cm);
        
        /// For setting the contact model properties from another contact model but without changing the 
        /// forces - just the properties.
        virtual void                  setNonForcePropsFrom(IContactModel *) { };
        
        /// Utility function that returns the property index based on its name, or 0 if property doesn't exist.
        /// Case insensitive by default.
        uint                          getPropertyIndex(const QString &name,Qt::CaseSensitivity cs=Qt::CaseInsensitive) const;// {name; cs; return 0;}

        /// Utility function that returns the property name given it's index.
        QString                       getPropertyName(uint index) const;
        
        // Major version of the contact model
        static UInt                   getMajorVersion();
        
        // Memory Allocation Customization
        // Changing this is very dangerous, as the calling program will make assumptions about
        //   where memory has been allocated to and from.
        void *operator new(size_t size);
        void *operator new(size_t size,const char *name,const char *file,unsigned line);
        void  operator delete(void *v);
        void  operator delete(void *v,const char *name,const char *file,unsigned line);
        typedef void *(*NewFunction)(size_t,const char *,const char *,unsigned);
        typedef void (*DeleteFunction)(void *,const char *,const char *,unsigned);
        typedef std::pair<NewFunction,DeleteFunction> AllocFunctions;
        static AllocFunctions setAllocFunctions(AllocFunctions afunc);
        static AllocFunctions getDefaultAllocFunctions();
        static AllocFunctions getAllocFunctions() { return AllocFunctions(newFunc_,deleteFunc_); }

    protected:
        static NewFunction    newFunc_;
        static DeleteFunction deleteFunc_;

        FArray<int,5>         cmEvents_;  ///< Set of events as defined in a specified order. The int refers to the location of the event in the ContactModelMechanicalList 
    };
} // namespace cmodelsxd

#pragma warning(pop)

// EoF