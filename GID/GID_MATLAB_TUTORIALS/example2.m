  close all
%  clearvars
% 
% 
% load("py_pedone_SNW_drained_putty_ascii_mesh_data.mat");
% load("py_pedone_SNW_drained_putty_ascii_results.mat");

vel = 0.001;
steps = [myResults.Time]';
displacements = steps * vel;
D = 0.5;
initial_position = D/2 + D/3;


%%

for tidx = 1:length(steps)

mm = myMesh(tidx).Nodes;


% 1 id, value
Q = myResults(tidx).STRESS_INV_Q;
P = myResults(tidx).STRESS_INV_P;


init_pos = [0,initial_position];% + displacements(tidx)];
init_pos2 = [0,initial_position - 7*D/10 + displacements(tidx)];


myElements = myMesh(tidx).Kratos_Triangle2D3_Mesh_1;

for ele_idx = 1:length(myElements)
myNodes = myElements(ele_idx,2:4);
myPositions = mm(myNodes',2:3);
myPos = mean(myPositions,1);
myElements(ele_idx,5:6)=myPos;
end


si_P = scatteredInterpolant(myElements(:,5),myElements(:,6),P(myElements(:,1),2),'linear','none');
si_Q = scatteredInterpolant(myElements(:,5),myElements(:,6),Q(myElements(:,1),2),'linear','none');


myP = si_P(init_pos);
myQ = si_Q(init_pos);

mat_PQ(tidx,1:2)=[myP,myQ];

myP2 = si_P(init_pos2);
myQ2 = si_Q(init_pos2);

mat_PQ2(tidx,1:2)=[myP2,myQ2];



end



close all
plot(mat_PQ(:,1),mat_PQ(:,2),'.')
xlabel('P [kPa]')
ylabel('Q [kPa]')

figure
hold on
plot(displacements,-mat_PQ(:,1),'DisplayName','P');
plot(displacements,mat_PQ(:,2),'DisplayName','Q');
legend('location','best')

figure
plot(mat_PQ2(:,1),mat_PQ2(:,2),'.')
xlabel('P [kPa]')
ylabel('Q [kPa]')

figure
hold on
plot(displacements,-mat_PQ2(:,1),'DisplayName','P');
plot(displacements,mat_PQ2(:,2),'DisplayName','Q');
legend('location','best')