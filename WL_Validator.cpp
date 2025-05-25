// File WL_Validator.cpp
// Validates the solution of the Warehouse Location Problem 
// with Store Incompatibilities. NOTE: indexes in the input file and
// the output list-format files  are 1-based, in the code they are 0-based

// Compile with: 
//    g++ -o WL_Validator.exe WL_Validator.cpp
// Run with: 
//    ./WL_Validator.exe <input_file> <solution_file>

#include <iostream>
#include <fstream>
#include <vector>

using namespace std;

class WL_Input 
{
public:
  WL_Input(string file_name);
  unsigned Stores() const { return stores; }
  unsigned Warehouses() const { return warehouses; }
  unsigned Capacity(unsigned w) const { return capacity[w]; }
  unsigned FixedCost(unsigned w) const { return fixed_cost[w]; }
  unsigned AmountOfGoods(unsigned s) const { return amount_of_goods[s]; }
  unsigned SupplyCost(unsigned s, unsigned w) const { return supply_cost[s][w]; }
  unsigned StoreIncompatibilities() const { return store_incompatibilities.size(); }
  pair<unsigned, unsigned> StoreIncompatibility(unsigned i) const { return store_incompatibilities[i]; }
 private:
  unsigned stores, warehouses;
  vector<unsigned> capacity;
  vector<unsigned> fixed_cost;
  vector<unsigned> amount_of_goods;
  vector<vector<unsigned>> supply_cost;
  vector<pair<unsigned, unsigned>> store_incompatibilities;
};

class WL_Output 
{
public:
  WL_Output(const WL_Input& i, string file_name);
  unsigned Supply(unsigned s, unsigned w) const { return supply[s][w]; }
  unsigned Load(unsigned w) const { return load[w]; }
  unsigned ResidualCapacity(unsigned w) const { return in.Capacity(w) - load[w]; }
  unsigned AssignedGoods(unsigned s) const { return assigned_goods[s]; }
  unsigned ResidualAmount(unsigned s) const { return in.AmountOfGoods(s) - assigned_goods[s]; }
  bool Compatible(unsigned w, unsigned s) const { return compatible[w][s]; }
  void Assign(unsigned s, unsigned w, unsigned q); // assign q goods of s to w
  unsigned ComputeCost() const;
  unsigned ComputeSupplyCost() const;
  unsigned ComputeOpeningCost() const;
  unsigned ComputeViolations() const;
  void PrintCosts(ostream& os) const;
  void PrintViolations(ostream& os) const;
private:
  const WL_Input& in;
  vector<vector<unsigned>> supply;   // main data
  vector<unsigned> assigned_goods;   // quantity of goods of each store already assigned to warehouses
  vector<unsigned> load;   // quantity of goods of each warehouse assigned to stores
  vector<vector<bool>> compatible; //  warehouse/store compatibility matrix based on current assignment
  // NOTE: opening is implicit, based on load > 0
};

WL_Input::WL_Input(string file_name)
{  
  const unsigned MAX_DIM = 100;
  unsigned w, s, s2;
  char ch, buffer[MAX_DIM];

  ifstream is(file_name);
  if(!is)
  {
    cerr << "Cannot open input file " <<  file_name << endl;
    exit(1);
  }
  
  is >> buffer >> ch >> warehouses >> ch;
  is >> buffer >> ch >> stores >> ch;
  
  capacity.resize(warehouses);
  fixed_cost.resize(warehouses);
  amount_of_goods.resize(stores);
  supply_cost.resize(stores,vector<unsigned>(warehouses));
  
  // read capacity
  is.ignore(MAX_DIM,'['); // read "... Capacity = ["
  for (w = 0; w < warehouses; w++)
    is >> capacity[w] >> ch;
  
  // read fixed costs  
  is.ignore(MAX_DIM,'['); // read "... FixedCosts = ["
  for (w = 0; w < warehouses; w++)
    is >> fixed_cost[w] >> ch;

  // read goods
  is.ignore(MAX_DIM,'['); // read "... Goods = ["
  for (s = 0; s < stores; s++)
    is >> amount_of_goods[s] >> ch;

  // read supply costs
  is.ignore(MAX_DIM,'['); // read "... SupplyCost = ["
  is >> ch; // read first '|'
  for (s = 0; s < stores; s++)
  {	 
    for (w = 0; w < warehouses; w++)
      is >> supply_cost[s][w] >> ch;
  }
  is >> ch >> ch;

  // read store incompatibilities
  unsigned incompatibilities;
  is >> buffer >> ch >> incompatibilities >> ch;  
  store_incompatibilities.resize(incompatibilities);
  is.ignore(MAX_DIM,'['); // read "... IncompatiblePairs = ["
  for (unsigned i = 0; i < incompatibilities; i++)
  {
    is >> ch >> s >> ch >> s2; 
	store_incompatibilities[i].first = s - 1;
	store_incompatibilities[i].second = s2 - 1;
  }
  is >> ch >> ch;
}

WL_Output::WL_Output(const WL_Input& my_in, string file_name)
  : in(my_in), supply(in.Stores(),vector<unsigned>(in.Warehouses(),0)), 
    assigned_goods(in.Stores(),0), load(in.Warehouses(),0), 
	compatible(in.Warehouses(),vector<bool>(in.Stores(),true))
{
  unsigned s, w, q;
  char ch;
  ifstream is(file_name);
  if(!is)
  {
    cerr << "Cannot open solution file " <<  file_name << endl;
    exit(1);
  }
  
  is >> ch;
  if (ch == '[') // matrix format
  {
    for (s = 0; s <  in.Stores(); s++)
      {
        is >> ch;
        for (w = 0; w <  in.Warehouses(); w++)
          {
            is >> q >> ch;
            Assign(s,w,q);
          }
      }
    is >> ch;
  }
  else // list format
  {
	 while (is >> ch >> s >> ch >> w >> ch >> q >> ch >> ch)
	 {
		Assign(s-1,w-1,q);
	 }	    
     is >> ch;
  }
}

void WL_Output::Assign(unsigned s, unsigned w, unsigned q)
{  
  unsigned i;
  if (s >= in.Stores())
  {
    cerr << "Store " << s << " out of range" << endl;
    exit(1);
  }
  if (w >= in.Warehouses())
  {
    cerr << "Warehouse " << w << " out of range" << endl;
    exit(1);
  }
  if (assigned_goods[s] + q > in.AmountOfGoods(s))
  {
    cerr << "Quantity " << q << " out of range for store " << s << endl;
    exit(1);
  }

  supply[s][w] += q;
  assigned_goods[s] += q;
  load[w] += q;
  for (i = 0; i < in.StoreIncompatibilities(); i++)
  {
	 if (in.StoreIncompatibility(i).first == s)
	    compatible[w][in.StoreIncompatibility(i).second] = false;
	 else if (in.StoreIncompatibility(i).second == s)
	    compatible[w][in.StoreIncompatibility(i).first] = false;
  }
}

unsigned WL_Output::ComputeCost() const
{
  return ComputeSupplyCost() + ComputeOpeningCost();
}

unsigned WL_Output::ComputeSupplyCost() const
{
  unsigned s, w, cost = 0;
  for (s = 0; s < in.Stores(); s++)
    for (w = 0; w < in.Warehouses(); w++)
      cost += supply[s][w] * in.SupplyCost(s,w);
  return cost;
}

unsigned WL_Output::ComputeOpeningCost() const
{
  unsigned w, cost = 0;
  for (w = 0; w < in.Warehouses(); w++)
    if (load[w] > 0)
      cost += in.FixedCost(w);
  return cost;
}

unsigned WL_Output::ComputeViolations() const
{
  unsigned s, w, i, violations = 0;
  for (s = 0; s < in.Stores(); s++)
    if (assigned_goods[s] < in.AmountOfGoods(s))
      violations++;
  for (w = 0; w < in.Warehouses(); w++)
    if (load[w] > in.Capacity(w))
      violations++;
  for (i = 0; i < in.StoreIncompatibilities(); i++)
     for (w = 0; w < in.Warehouses(); w++)
	    if (supply[in.StoreIncompatibility(i).first][w] > 0 
		 && supply[in.StoreIncompatibility(i).second][w] > 0)
		violations++; 
  return violations;
}

void WL_Output::PrintCosts(ostream& os) const
{
  unsigned s, w, cost = 0;
  for (s = 0; s < in.Stores(); s++)
    for (w = 0; w < in.Warehouses(); w++)
	   if (supply[s][w] > 0)
	     {
            cost += supply[s][w] * in.SupplyCost(s,w);
			os << "Moving " << supply[s][w] << " goods from warehourse " << w+1 
			   << " to store " << s+1 << ", cost " << supply[s][w] << "x" 
			   << in.SupplyCost(s,w) << " = " << supply[s][w] * in.SupplyCost(s,w)
		       << " (" << cost << ")" << endl;
		 }
  for (w = 0; w < in.Warehouses(); w++)
    if (load[w] > 0)
	{
      cost += in.FixedCost(w);
	  os << "Opening warehouse " << w+1 << ", cost " << in.FixedCost(w) 
	     << " (" << cost << ")" << endl;
	}
}	
	
void WL_Output::PrintViolations(ostream& os) const
{
  unsigned s, w, i;
  for (s = 0; s < in.Stores(); s++)
    if (assigned_goods[s] < in.AmountOfGoods(s))
      os << "Goods of store " << s+1 << " are not moved completely (ammount = " 
         << in.AmountOfGoods(s) << ", moved = " << assigned_goods[s] << ")" << endl;
  for (w = 0; w < in.Warehouses(); w++)
    if (load[w] > in.Capacity(w))
      os << "Goods of warehouses " << w+1 << " exceed its capacity (capacity = " 
         << in.Capacity(w) << ", moved = " << load[w] << ")" << endl;
  for (i = 0; i < in.StoreIncompatibilities(); i++)
    for (w = 0; w < in.Warehouses(); w++)
      if (supply[in.StoreIncompatibility(i).first][w] > 0 
          && supply[in.StoreIncompatibility(i).second][w] > 0)
        os << "Warehouses " << w+1 << " supplies incompatible stores " 
           << in.StoreIncompatibility(i).first+1 << " and "
           << in.StoreIncompatibility(i).second+1 << endl;
}

int main(int argc, char* argv[])
{
  string instance;
  if (argc != 3)
    {
      cerr << "Usage: " << argv[0] << " <input_file> <solution_file>" << endl
           << "Input file in .dzn format, solution file either in matrix format (within []) or list format (within {})." << endl;
      exit(1);
    }

  WL_Input in(argv[1]);
  WL_Output out(in, argv[2]);
  
  out.PrintCosts(cout);
  out.PrintViolations(cout);
  cout << "Number of violations: " << out.ComputeViolations() << endl;
  cout << "Cost: " << out.ComputeCost() << " = " << out.ComputeSupplyCost() << " (supply cost) + " 
       << out.ComputeOpeningCost() << " (opening cost)" << endl << endl;
  return 0;
}

