#pragma once
// contactmodelthermal.h

#include "contactmodel.h"
#include "contactmodel/interface/icontactmodelthermal.h"

#pragma warning(push)
#pragma warning(disable:4251)

namespace itascaxd
{
  class IContactThermal;
  class IContactMechanical;
}

namespace cmodelsxd
{
  using namespace itasca;
  using namespace itascaxd;

  class ContactModelThermalState : public ContactModelState
  {
  public:
    ContactModelThermalState() : power_(0.0), length_(0.0),
      end1Temperature_(0.0), end2Temperature_(0.0), tempInc_(0.0) 
    { };

    virtual ~ContactModelThermalState() { };

    virtual const IContactThermal    *getThermalContact()    const=0;
    virtual const IContactMechanical *getMechanicalContact() const=0;
    virtual const IProgram *          getProgram()           const=0;

    double      power_;             // current total power (from 1 to 2) at this contact (computed by the contact model) 
    double      length_;            // length of the pipe 
    double      end1Temperature_;   // temperature in reservoir 1 
    double      end2Temperature_;   // temperature in reservoir 2 
    double      tempInc_;           // temperature increment in contact     
  };

  class CONTACTMODEL_EXPORT ContactModelThermal : public IContactModelThermal
                                                 ,public ContactModel
  {
  public:
    ContactModelThermal();
    virtual ~ContactModelThermal();

    static const char *           getPluginPrefix() { return "contactmodelthermal"; }
    static const char *           getPluginDirectory() { return "contactmodels/thermal"; }

    // IContactModelThermal functions.

    virtual IContactModel * getContactModel() {return this;}
    virtual const IContactModel * getContactModel() const {return this;}

    // Returns true if the property was actually updated in the contact model.
    virtual bool     endPropertyUpdated(const QString &name,const IContactThermal *c)=0;

    // For the contact model state
    virtual bool    validate(ContactModelThermalState *state,const double &timestep)=0;
    virtual bool    checkActivity(ContactModelThermalState *d) const=0;

    // Returns Activity Distance (defaults to 0.0) -- distance between objects that contact is considered active.
    virtual double   getActivityDistance() const {return 0.0;}

    // Updates power from end1 to end2.
    // Returns true if contact is active
    virtual bool updatePower(ContactModelThermalState *state,const double &timestep)=0;

    // Returns timestep limits (defaults to (0.0,infinity))
    // These are further timestep restrictions that the contact model can place on the simulation, over and above those implied by stiffness.
    virtual DVect2   getTimestepLimits(ContactModelThermalState *,const double &) const { return DVect2(0.0,limits<double>::max());}

    // Returns the Resistance per unit length
    virtual double  getEffectiveResistance() const {return 0.0;}

    // For contact specific plotting
    virtual void getSphereList(const IContact *con,std::vector<DVect> *pos,std::vector<double> *rad,std::vector<double> *val) { con; pos; rad; val; }
#ifdef THREED
    virtual void getDiskList(const IContact *con,std::vector<DVect> *pos,std::vector<DVect> *normal,std::vector<double> *radius,std::vector<double> *val) { con; pos; normal; radius; val; }
#endif
    virtual void getCylinderList(const IContact *con,std::vector<DVect> *bot,std::vector<DVect> *top,std::vector<double> *radlow,std::vector<double> *radhi,std::vector<double> *val) { con; bot; top; radlow; radhi; val; }


  };
} // namespace cmodel

#pragma warning(pop)


// EoF